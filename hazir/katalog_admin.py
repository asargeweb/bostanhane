"""
Bostanhane — katalog yönetim paneli

Bu dosya `katalog/admin.py` yerine geçer.

İki ayrı liste var ve günlük iş ikincisinde yürüyor:

**Ürünler** — ürünün tanımı. Birim, tartılı mı, kanallar, raf ömrü. Nadiren değişir.
**Mağaza ürünleri** — fiyat ve stok durumu. Her gün değişir, listeden toplu düzenlenir.

Günlük iş Ürünler listesinde de yapılabilir: her satırda fiyat, satışta ve stok
"düzenle" / "ekle / çıkar" düğmesiyle açılır, bir kerede kaydedilir. Stok yalnızca
stok hareketiyle değişir; her hareket "Stok hareketleri" defterinde kalır.
"""

from decimal import Decimal, InvalidOperation
from urllib.parse import urlencode

from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.db.models import BooleanField, Count, DecimalField, IntegerField, OuterRef, Subquery, Value
from django.db.models.functions import Coalesce
from django.utils.html import format_html, format_html_join
from django.utils.safestring import mark_safe

from core.admin_araclar import MagazaKisitliAdmin
from core.araclar import para_yaz

from .models import Birim, Kategori, MagazaUrun, StokHareketi, Urun


@admin.register(Kategori)
class KategoriAdmin(admin.ModelAdmin):
    list_display = ("ad", "sira", "urun_adedi", "aktif")
    list_editable = ("sira", "aktif")
    search_fields = ("ad",)
    prepopulated_fields = {"slug": ("ad",)}

    @admin.display(description="aktif ürün")
    def urun_adedi(self, nesne):
        return nesne.urun_sayisi


@admin.register(Birim)
class BirimAdmin(admin.ModelAdmin):
    list_display = ("ad", "kisaltma", "kesirli", "urun_adedi", "sira", "aktif")
    list_editable = ("kisaltma", "kesirli", "sira", "aktif")
    search_fields = ("ad", "kisaltma")

    @admin.display(description="ürün sayısı")
    def urun_adedi(self, nesne):
        return nesne.urunler.count()

    def has_delete_permission(self, request, nesne=None):
        # Ürünü olan birim zaten silinemez (PROTECT); kullanılmayanı da yalnızca
        # süper admin siler — yanlışlıkla silinen birim Excel aktarımını bozar.
        return request.user.is_superuser


class MagazaUrunSatiri(admin.TabularInline):
    """Ürün sayfasından mağaza fiyatlarını görmek ve girmek için."""
    model = MagazaUrun
    extra = 0
    fields = ("magaza", "fiyat", "eski_fiyat", "durum", "aktif", "stok")
    readonly_fields = ("stok",)
    verbose_name = "mağaza fiyatı"
    verbose_name_plural = "mağaza fiyatları"


def fiyat_yaz(tutar):
    """Decimal → '1.250,50' — fiyat kutusunun içi için, ₺ işaretsiz. Biçim para_yaz'dan."""
    return para_yaz(tutar).removesuffix(" ₺")


def miktar_yaz(miktar):
    """Decimal → '10' · '2,5' · '0,25' — gereksiz sıfırlar olmadan."""
    return f"{miktar.normalize():f}".replace(".", ",")


def sayi_oku(metin, basamak):
    """
    Listeye elle yazılan sayıyı çözer. Hem '32,90' hem '32.90' hem '1.250,50'
    yazılabilir; ₺ işareti ve boşluk yok sayılır. Boşsa None, okunamazsa ValueError.
    """
    metin = metin.replace("₺", "").replace(" ", "").strip()
    if not metin:
        return None
    if "," in metin:
        metin = metin.replace(".", "").replace(",", ".")
    try:
        return Decimal(metin).quantize(Decimal(1).scaleb(-basamak))
    except InvalidOperation:
        raise ValueError


def fiyat_oku(metin):
    tutar = sayi_oku(metin, 2)
    if tutar is not None and tutar <= 0:
        raise ValueError
    return tutar


class FiyatMagazasiSuzgeci(admin.SimpleListFilter):
    """
    Ürünler listesindeki fiyat ve stok sütunları hangi mağazayı göstersin.

    Ürünü süzmez, yalnızca mağaza seçer: fiyat ve stok mağaza başına tutulur
    (Karaman'da domates Beyşehir'den farklı olabilir). Yalnızca süper admin
    görür; mağaza personeli her zaman kendi mağazasını görür.
    """
    title = "fiyat mağazası"
    parameter_name = "fiyat_magaza"

    def lookups(self, request, model_admin):
        from core.models import Magaza
        return [(str(m.pk), m.ad) for m in Magaza.objects.filter(aktif=True)]

    def queryset(self, request, queryset):
        return queryset


# Ürünler listesindeki "ekle / çıkar" türleri ve miktarın yönü.
# Mal kabul her zaman ekler, fire her zaman çıkarır: işaret yazmayı unutmak
# stoğu ters yöne götürmesin. Sayım düzeltmesi yazıldığı gibi (+ ya da −) uygulanır.
STOK_TURLERI = [
    (StokHareketi.Tur.MAL_KABUL, "Mal kabul (+)", 1),
    (StokHareketi.Tur.FIRE, "Fire (−)", -1),
    (StokHareketi.Tur.SAYIM, "Sayım düzeltmesi (±)", None),
]


def duzenle_hucresi(metin, dugme, alan):
    """
    Satır içi düzenleme hücresi: önce düz yazı + düğme, düğmeye basınca alanlar.
    Alanlar `disabled` başlar; kapalı alan forma gönderilmez, yani açılmamış
    satır Kaydet'le değişmez — yanlışlıkla giriş olmasın diye.

    Açılan alanın yanında kendi Kaydet düğmesi var: uzun listede her satırdan sonra
    sayfanın sonuna inmek gerekmesin. Listenin alttaki Kaydet'iyle aynı işi yapar
    (`_save`), yani o anda açık olan bütün satırlar birlikte kaydedilir.
    """
    return format_html(
        '<span class="duzenle-hucre">'
        '<span class="duzenle-metin">{} '
        '<button type="button" class="button duzenle-ac">{}</button></span>'
        '<span class="duzenle-alan" hidden>{} '
        '<button type="submit" name="_save" class="button default">Kaydet</button> '
        '<button type="button" class="button duzenle-vazgec">vazgeç</button></span>'
        '</span>', metin, dugme, alan)


@admin.register(Urun)
class UrunAdmin(admin.ModelAdmin):
    list_display = ("ad", "kategori", "birim_kisa", "fiyat_kutusu", "stok_kutusu",
                    "tartili_isareti", "kanallar_metni", "raf_omru_gun", "aktif")
    list_filter = ("kategori", "birim", "aktif", "tartili_mi", "yerel_satis",
                   "kargo_satis", "kurumsal_satis", "soguk_zincir", "abonelige_uygun")
    search_fields = ("ad", "aciklama", "mevsim")
    list_select_related = ("kategori", "birim")
    prepopulated_fields = {"slug": ("ad",)}
    list_editable = ("aktif",)
    inlines = [MagazaUrunSatiri]
    fieldsets = (
        ("Ürün", {"fields": ("kategori", "ad", "slug", "aciklama", "gorsel", "sira", "aktif")}),
        ("Satış biçimi", {
            "description": "Tartılı üründe sepette provizyon alınır, kesin tutar tartımdan "
                           "sonra çekilir. Tartılı ürün kesirli birimle (kilogram) satılır. "
                           "Listede olmayan birimi KATALOG → Birimler'den ekleyin.",
            "fields": (("birim", "tartili_mi"), ("satis_adimi", "ambalaj_bilgisi")),
        }),
        ("Satış kanalları", {
            "description": "Kargo için dört şart birden sağlanmalı: raf ömrü en az 14 gün, "
                           "soğuk zincir istemez, tartısız, ambalajı dayanıklı. "
                           "Kaydetmeye çalıştığınızda sistem bunu denetler.",
            "fields": (("yerel_satis", "kargo_satis"), ("kurumsal_satis", "abonelige_uygun")),
        }),
        ("Saklama ve uyarı", {
            "fields": (("raf_omru_gun", "soguk_zincir"), "mevsim", "uyari_metni"),
        }),
    )
    actions = ["magazalara_ekle"]

    class Media:
        js = ["katalog/fiyat_duzenle.js"]

    # -- fiyat ve stok sütunları -------------------------------------------
    # Fiyat ve stok MagazaUrun'da durur, Urun'da değil; list_editable yalnızca
    # modelin kendi alanlarını kabul ettiği için kutuları elle çiziyor, kaydı
    # changelist_view'da kendimiz yapıyoruz. Amaç: ürünü, fiyatını ve stoğunu
    # tek ekranda görüp girmek.

    def fiyat_magazasi(self, request):
        from core.models import Magaza
        if not getattr(request.user, "tum_magazalari_gorur", request.user.is_superuser):
            return getattr(request.user, "magaza", None)
        secilen = request.GET.get(FiyatMagazasiSuzgeci.parameter_name)
        magazalar = Magaza.objects.filter(aktif=True)
        if secilen and secilen.isdigit():
            return magazalar.filter(pk=secilen).first()
        return magazalar.order_by("pk").first()

    def get_list_filter(self, request):
        if getattr(request.user, "tum_magazalari_gorur", request.user.is_superuser):
            return (FiyatMagazasiSuzgeci, *self.list_filter)
        return self.list_filter

    def get_queryset(self, request):
        # Satır başına ayrı sorgu olmasın diye mağaza bilgisini tek sorguda ekliyoruz.
        qs = super().get_queryset(request)
        magaza = self.fiyat_magazasi(request)
        qs = qs.annotate(_duzenlenebilir=Value(
            request.user.has_perm("katalog.change_magazaurun"), output_field=BooleanField()))
        if magaza is None:
            return qs.annotate(_fiyat=Value(None, output_field=DecimalField()),
                               _satista=Value(False, output_field=BooleanField()),
                               _stok=Value(None, output_field=DecimalField()),
                               _fiyat_magazasi=Value(None, output_field=IntegerField()))
        kayit = MagazaUrun.objects.filter(magaza=magaza, urun=OuterRef("pk"))
        return qs.annotate(_fiyat=Subquery(kayit.values("fiyat")[:1]),
                           _satista=Coalesce(Subquery(kayit.values("aktif")[:1]), False),
                           _stok=Subquery(kayit.values("stok")[:1]),
                           _fiyat_magazasi=Value(magaza.pk, output_field=IntegerField()))

    @admin.display(description="birim", ordering="birim__sira")
    def birim_kisa(self, nesne):
        return nesne.birim.kisaltma

    @admin.display(description="fiyat · satışta")
    def fiyat_kutusu(self, nesne):
        if getattr(nesne, "_fiyat_magazasi", None) is None:
            return "—"
        birim = nesne.birim.kisaltma
        deger = fiyat_yaz(nesne._fiyat) if nesne._fiyat is not None else ""
        if deger:
            metin = format_html('<b>{} ₺</b> / {}', deger, birim)
        else:
            metin = format_html('<span style="color:#B23A24">{}</span>', "fiyat yok")
        if nesne._satista:
            satista = format_html('<span style="color:#1F5132">{}</span>', "✓ satışta")
        else:
            satista = format_html('<span style="color:#8A8A8A">{}</span>', "satışta değil")
        if not nesne._duzenlenebilir:
            return format_html("{} · {}", metin, satista)
        alan = format_html(
            '<input type="text" name="fiyat_{}" value="{}" size="7" inputmode="decimal"'
            ' disabled style="text-align:right"> ₺ / {} '
            '<label><input type="checkbox" name="satista_{}" disabled{}> satışta</label>'
            '<input type="hidden" name="fiyat_ilk_{}" value="{}">'
            '<input type="hidden" name="satista_ilk_{}" value="{}">',
            nesne.pk, deger, birim,
            nesne.pk, mark_safe(" checked") if nesne._satista else "",
            nesne.pk, deger, nesne.pk, "1" if nesne._satista else "")
        return duzenle_hucresi(format_html("{} · {}", metin, satista),
                               "düzenle" if deger else "fiyat gir", alan)

    @admin.display(description="stok")
    def stok_kutusu(self, nesne):
        if getattr(nesne, "_fiyat_magazasi", None) is None:
            return "—"
        birim = nesne.birim.kisaltma
        if nesne._stok is None:
            metin = format_html('<span style="color:#8A8A8A" title="{}">{}</span>',
                                "Stok takip edilmiyor; sınırsız satılır.", "takip yok")
        elif nesne._stok <= 0:
            metin = format_html('<b style="color:#B23A24">0 {}</b>', birim)
        else:
            metin = format_html("<b>{} {}</b>", miktar_yaz(nesne._stok), birim)
        if not nesne._duzenlenebilir:
            return metin
        secenekler = format_html_join(
            "", '<option value="{}">{}</option>', ((t, ad) for t, ad, _ in STOK_TURLERI))
        alan = format_html(
            '<select name="stok_tur_{}" disabled>{}</select> '
            '<input type="text" name="stok_{}" size="5" inputmode="decimal" placeholder="miktar"'
            ' disabled style="text-align:right"> {}',
            nesne.pk, secenekler, nesne.pk, birim)
        return duzenle_hucresi(metin, "ekle / çıkar", alan)

    def changelist_view(self, request, extra_context=None):
        if (request.method == "POST" and "_save" in request.POST
                and request.user.has_perm("katalog.change_magazaurun")):
            self.satirlari_kaydet(request)
        extra_context = {**(extra_context or {}),
                         "kategori_sekmeleri": self.kategori_sekmeleri(request)}
        return super().changelist_view(request, extra_context)

    def kategori_sekmeleri(self, request):
        """
        Listenin üstündeki "Tümü · Sebze · Meyve …" sekmeleri. 50 ürünlük liste uzun;
        fiyat girerken kategori kategori gitmek kolay. Sağdaki süzgeçle aynı parametreyi
        kullanıyor, diğer süzgeçler ve mağaza seçimi korunuyor.
        """
        anahtar = "kategori__id__exact"
        secili = request.GET.get(anahtar, "")
        temel = {k: v for k, v in request.GET.items() if k not in (anahtar, "p")}
        sayilar = dict(Urun.objects.values_list("kategori").annotate(adet=Count("pk")))

        def adres(deger):
            return "?" + urlencode({**temel, anahtar: deger} if deger else temel)

        sekmeler = [{"ad": "Tümü", "adet": sum(sayilar.values()), "adres": adres(""),
                     "secili": not secili}]
        for kategori in Kategori.objects.all():
            sekmeler.append({"ad": kategori.ad, "adet": sayilar.get(kategori.pk, 0),
                             "adres": adres(str(kategori.pk)), "secili": secili == str(kategori.pk)})
        return sekmeler

    def satirlari_kaydet(self, request):
        magaza = self.fiyat_magazasi(request)
        if magaza is None:
            return
        sayac = {"fiyat": 0, "acilan": 0, "kapanan": 0, "stok": 0}
        hatalar = []
        for anahtar, metin in request.POST.items():
            if anahtar.startswith("fiyat_") and not anahtar.startswith("fiyat_ilk_"):
                hata = self.fiyat_satiri(request, magaza, anahtar.removeprefix("fiyat_"),
                                         metin, sayac)
            elif anahtar.startswith("stok_") and not anahtar.startswith("stok_tur_"):
                hata = self.stok_satiri(request, magaza, anahtar.removeprefix("stok_"),
                                        metin, sayac)
            else:
                continue
            if hata:
                hatalar.append(hata)
        parcalar = []
        if sayac["fiyat"]:
            parcalar.append(f"{sayac['fiyat']} ürünün fiyatı kaydedildi")
        if sayac["acilan"]:
            parcalar.append(f"{sayac['acilan']} ürün satışa açıldı")
        if sayac["kapanan"]:
            parcalar.append(f"{sayac['kapanan']} ürün satıştan çekildi")
        if sayac["stok"]:
            parcalar.append(f"{sayac['stok']} ürünün stoğu güncellendi")
        if parcalar:
            self.message_user(request, ", ".join(parcalar) + f" ({magaza.ad}).")
        for hata in hatalar:
            self.message_user(request, f"Kaydedilmedi — {hata}", level=messages.ERROR)

    def fiyat_satiri(self, request, magaza, pk, metin, sayac):
        """Açılan fiyat satırını yazar. Hata varsa mesajı döner."""
        if not pk.isdigit():
            return None
        # Yalnızca değiştirilen alanlar yazılır; başka biri aynı anda
        # "Mağaza ürünleri"nden değiştirdiyse üzerine basmayalım.
        fiyat_degisti = metin.strip() != request.POST.get(f"fiyat_ilk_{pk}", "").strip()
        # İşaretsiz onay kutusu forma gelmez; satırı fiyat kutusundan tanıyoruz.
        satista = f"satista_{pk}" in request.POST
        satista_degisti = satista != bool(request.POST.get(f"satista_ilk_{pk}"))
        if not (fiyat_degisti or satista_degisti):
            return None
        urun = Urun.objects.filter(pk=pk).first()
        if urun is None:
            return None
        kayit, _ = MagazaUrun.objects.get_or_create(magaza=magaza, urun=urun)
        # Önce fiyat, sonra satışta, sonra tek denetim: aynı kaydetmede
        # fiyat girip ürünü satışa açmak çalışsın.
        if fiyat_degisti:
            try:
                kayit.fiyat = fiyat_oku(metin)
            except ValueError:
                return f"{urun.ad}: “{metin}” fiyat olarak okunamadı"
        if satista_degisti:
            kayit.aktif = satista
        try:
            kayit.full_clean()
        except ValidationError as hata:
            return f"{urun.ad}: " + " ".join(
                m for mesajlar in hata.message_dict.values() for m in mesajlar)
        kayit.save()
        sayac["fiyat"] += 1 if fiyat_degisti else 0
        if satista_degisti:
            sayac["acilan" if satista else "kapanan"] += 1
        return None

    def stok_satiri(self, request, magaza, pk, metin, sayac):
        """Açılan stok satırını deftere işler. Hata varsa mesajı döner."""
        if not pk.isdigit() or not metin.strip():
            return None
        urun = Urun.objects.filter(pk=pk).select_related("birim").first()
        if urun is None:
            return None
        try:
            miktar = sayi_oku(metin, 3)
        except ValueError:
            return f"{urun.ad}: “{metin}” miktar olarak okunamadı"
        if not miktar:
            return None
        if not urun.birim.kesirli and miktar % 1:
            return f"{urun.ad}: {urun.birim.ad.lower()} kesirli girilemez, tam sayı yazın"
        tur = request.POST.get(f"stok_tur_{pk}")
        yon = {t: y for t, _, y in STOK_TURLERI}
        if tur not in yon:
            return f"{urun.ad}: stok hareketinin türü seçilmedi"
        if yon[tur] is not None:
            miktar = abs(miktar) * yon[tur]
        kayit, _ = MagazaUrun.objects.get_or_create(magaza=magaza, urun=urun)
        try:
            kayit.stok_degistir(miktar, tur, kullanici=request.user)
        except ValidationError as hata:
            return f"{urun.ad}: " + " ".join(hata.messages)
        sayac["stok"] += 1
        return None

    @admin.display(description="tartılı", boolean=True, ordering="tartili_mi")
    def tartili_isareti(self, nesne):
        return nesne.tartili_mi

    @admin.action(description="Seçili ürünleri bütün mağazalara ekle (fiyatsız)")
    def magazalara_ekle(self, request, queryset):
        """
        Yeni ürün tanımlandığında her mağazaya fiyatsız kayıt açar.
        Fiyatlar sonra "Mağaza ürünleri" listesinden toplu girilir.
        """
        from core.models import Magaza

        magazalar = Magaza.objects.filter(aktif=True)
        if not getattr(request.user, "tum_magazalari_gorur", request.user.is_superuser):
            magazalar = magazalar.filter(pk=getattr(request.user, "magaza_id", None))

        eklenen = 0
        for urun in queryset:
            for magaza in magazalar:
                _, yeni = MagazaUrun.objects.get_or_create(magaza=magaza, urun=urun)
                eklenen += 1 if yeni else 0
        self.message_user(
            request,
            f"{eklenen} mağaza-ürün kaydı açıldı. Fiyatları “Mağaza ürünleri” "
            f"listesinden girebilirsiniz." if eklenen
            else "Yeni kayıt eklenmedi; hepsi zaten vardı.")


class StokHareketiSatiri(admin.TabularInline):
    """Mağaza ürünü sayfasında son stok hareketleri — yalnızca okunur."""
    model = StokHareketi
    extra = 0
    fields = ("olusturuldu", "tur", "miktar", "onceki_stok", "sonraki_stok", "kullanici", "aciklama")
    readonly_fields = fields
    can_delete = False
    verbose_name_plural = "stok hareketleri"

    def has_add_permission(self, request, nesne=None):
        return False


@admin.register(MagazaUrun)
class MagazaUrunAdmin(MagazaKisitliAdmin, admin.ModelAdmin):
    magaza_yolu = "magaza"

    list_display = ("urun_adi", "kategori_adi", "birim_adi", "fiyat",
                    "fiyat_gosterim", "stok_gosterim", "durum", "aktif", "magaza")
    list_editable = ("fiyat", "durum", "aktif")
    list_filter = ("magaza", "aktif", "durum", "urun__kategori", "urun__tartili_mi")
    search_fields = ("urun__ad", "urun__kategori__ad")
    list_select_related = ("urun", "urun__kategori", "urun__birim", "magaza")
    autocomplete_fields = ("urun",)
    list_per_page = 60
    # Stok elle yazılmaz: her değişim deftere girsin diye yalnızca
    # Ürünler listesindeki "ekle / çıkar" ile değişir.
    readonly_fields = ("stok",)
    inlines = [StokHareketiSatiri]
    fieldsets = (
        (None, {"fields": ("magaza", "urun")}),
        ("Fiyat", {"fields": (("fiyat", "eski_fiyat"),)}),
        ("Satış", {"fields": ("durum", "aktif", "gunluk_limit", "sira")}),
        ("Stok", {"fields": ("stok",)}),
    )
    actions = ["satisa_ac", "satisi_kapat", "tukendi_isaretle", "stok_takibini_kapat"]

    @admin.display(description="ürün", ordering="urun__ad")
    def urun_adi(self, nesne):
        return nesne.urun.ad

    @admin.display(description="kategori", ordering="urun__kategori__sira")
    def kategori_adi(self, nesne):
        return nesne.urun.kategori.ad

    @admin.display(description="birim")
    def birim_adi(self, nesne):
        return nesne.urun.satis_adimi_metni

    @admin.display(description="müşteriye görünen")
    def fiyat_gosterim(self, nesne):
        """Para birimi tutardan sonra yazılır: 42,90 ₺"""
        if nesne.fiyat is None:
            # format_html argümansız çağrılamaz (Django 5+); metni parametre veriyoruz.
            return format_html('<span style="color:#B23A24">{}</span>', "fiyat girilmedi")
        metin = fiyat_yaz(nesne.fiyat)
        if nesne.indirimli_mi:
            return format_html(
                '<s style="color:#8A8A8A">{} ₺</s> <b style="color:#1F5132">{} ₺</b>'
                ' <span style="color:#D98A2B">%{}</span>',
                fiyat_yaz(nesne.eski_fiyat), metin, nesne.indirim_orani)
        return format_html("<b>{} ₺</b>", metin)

    @admin.display(description="stok", ordering="stok")
    def stok_gosterim(self, nesne):
        if nesne.stok is None:
            return "takip yok"
        return f"{miktar_yaz(nesne.stok)} {nesne.urun.birim.kisaltma}"

    # -- işlemler ----------------------------------------------------------
    @admin.action(description="Satışa aç (fiyatı olanlar)")
    def satisa_ac(self, request, queryset):
        uygun = queryset.filter(fiyat__isnull=False)
        eksik = queryset.filter(fiyat__isnull=True).count()
        adet = uygun.update(aktif=True, durum=MagazaUrun.Durum.SATISTA)
        mesaj = f"{adet} ürün satışa açıldı."
        if eksik:
            mesaj += f" {eksik} ürün fiyatsız olduğu için atlandı."
        self.message_user(request, mesaj)

    @admin.action(description="Satışı kapat")
    def satisi_kapat(self, request, queryset):
        adet = queryset.update(aktif=False)
        self.message_user(request, f"{adet} ürünün satışı kapatıldı.")

    @admin.action(description="Tükendi olarak işaretle")
    def tukendi_isaretle(self, request, queryset):
        adet = queryset.update(durum=MagazaUrun.Durum.TUKENDI)
        self.message_user(request, f"{adet} ürün tükendi olarak işaretlendi.")

    @admin.action(description="Stok takibini kapat (sınırsız sat)")
    def stok_takibini_kapat(self, request, queryset):
        adet = sum(1 for kayit in queryset if kayit.stok_takibini_kapat(request.user))
        self.message_user(request, f"{adet} ürünün stok takibi kapatıldı; artık sınırsız satılır.")


@admin.register(StokHareketi)
class StokHareketiAdmin(MagazaKisitliAdmin, admin.ModelAdmin):
    """
    Stok defteri. Yalnızca okunur: hareketler düzeltilmez, silinmez; yanlış giriş
    Ürünler listesinden ters bir sayım düzeltmesiyle dengelenir.
    """
    magaza_yolu = "magaza_urun__magaza"

    list_display = ("olusturuldu", "urun_adi", "tur", "miktar_gosterim",
                    "onceki_gosterim", "sonraki_gosterim", "kullanici", "magaza_adi")
    list_filter = ("tur", "magaza_urun__magaza", "magaza_urun__urun__kategori")
    search_fields = ("magaza_urun__urun__ad", "aciklama")
    list_select_related = ("magaza_urun__urun__birim", "magaza_urun__magaza", "kullanici")
    date_hierarchy = "olusturuldu"
    list_per_page = 100

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, nesne=None):
        return False

    def has_delete_permission(self, request, nesne=None):
        return False

    def _birim(self, nesne):
        return nesne.magaza_urun.urun.birim.kisaltma

    @admin.display(description="ürün", ordering="magaza_urun__urun__ad")
    def urun_adi(self, nesne):
        return nesne.magaza_urun.urun.ad

    @admin.display(description="mağaza")
    def magaza_adi(self, nesne):
        return nesne.magaza_urun.magaza.ad

    @admin.display(description="miktar", ordering="miktar")
    def miktar_gosterim(self, nesne):
        renk = "#1F5132" if nesne.miktar > 0 else "#B23A24"
        isaret = "+" if nesne.miktar > 0 else ""
        return format_html('<b style="color:{}">{}{} {}</b>', renk, isaret,
                           miktar_yaz(nesne.miktar), self._birim(nesne))

    @admin.display(description="önceki")
    def onceki_gosterim(self, nesne):
        if nesne.onceki_stok is None:
            return "takip yok"
        return f"{miktar_yaz(nesne.onceki_stok)} {self._birim(nesne)}"

    @admin.display(description="sonraki")
    def sonraki_gosterim(self, nesne):
        if nesne.sonraki_stok is None:
            return "takip yok"
        return f"{miktar_yaz(nesne.sonraki_stok)} {self._birim(nesne)}"
