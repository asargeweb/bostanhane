"""
Bostanhane — katalog yönetim paneli

Bu dosya `katalog/admin.py` yerine geçer.

İki ayrı liste var ve günlük iş ikincisinde yürüyor:

**Ürünler** — ürünün tanımı. Birim, tartılı mı, kanallar, raf ömrü. Nadiren değişir.
**Mağaza ürünleri** — fiyat ve stok durumu. Her gün değişir, listeden toplu düzenlenir.

Fiyat girişi listede yapılır: `list_editable` sayesinde fiyat, durum ve satışta
kutucuğu tek ekranda doldurulup bir kerede kaydedilir. 50 ürünün fiyatını tek tek
sayfa açarak girmek saçma olurdu.
"""

from decimal import Decimal, InvalidOperation

from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.db.models import BooleanField, DecimalField, IntegerField, OuterRef, Subquery, Value
from django.utils.html import format_html

from core.admin_araclar import MagazaKisitliAdmin

from .models import Birim, Kategori, MagazaUrun, Urun


@admin.register(Kategori)
class KategoriAdmin(admin.ModelAdmin):
    list_display = ("ad", "sira", "urun_adedi", "aktif")
    list_editable = ("sira", "aktif")
    search_fields = ("ad",)
    prepopulated_fields = {"slug": ("ad",)}

    @admin.display(description="aktif ürün")
    def urun_adedi(self, nesne):
        return nesne.urun_sayisi


class MagazaUrunSatiri(admin.TabularInline):
    """Ürün sayfasından mağaza fiyatlarını görmek ve girmek için."""
    model = MagazaUrun
    extra = 0
    fields = ("magaza", "fiyat", "eski_fiyat", "durum", "aktif")
    verbose_name = "mağaza fiyatı"
    verbose_name_plural = "mağaza fiyatları"


def fiyat_yaz(tutar):
    """Decimal → '1.250,50' (Türkçe ondalık virgülü)."""
    return f"{tutar:,.2f}".replace(",", "#").replace(".", ",").replace("#", ".")


def fiyat_oku(metin):
    """
    Listeye elle yazılan fiyatı çözer. Hem '32,90' hem '32.90' hem '1.250,50'
    yazılabilir; ₺ işareti ve boşluk yok sayılır. Boşsa None, okunamazsa ValueError.
    """
    metin = metin.replace("₺", "").replace(" ", "").strip()
    if not metin:
        return None
    if "," in metin:
        metin = metin.replace(".", "").replace(",", ".")
    try:
        tutar = Decimal(metin).quantize(Decimal("0.01"))
    except InvalidOperation:
        raise ValueError
    if tutar <= 0:
        raise ValueError
    return tutar


class FiyatMagazasiSuzgeci(admin.SimpleListFilter):
    """
    Ürünler listesindeki fiyat sütunu hangi mağazanın fiyatını göstersin.

    Ürünü süzmez, yalnızca mağaza seçer: fiyat mağaza başına tutulur
    (Karaman'da domates Beyşehir'den farklı olabilir). Yalnızca süper admin
    görür; mağaza personeli her zaman kendi mağazasının fiyatını görür.
    """
    title = "fiyat mağazası"
    parameter_name = "fiyat_magaza"

    def lookups(self, request, model_admin):
        from core.models import Magaza
        return [(str(m.pk), m.ad) for m in Magaza.objects.filter(aktif=True)]

    def queryset(self, request, queryset):
        return queryset


@admin.register(Urun)
class UrunAdmin(admin.ModelAdmin):
    list_display = ("ad", "kategori", "satis_bilgisi", "fiyat_kutusu", "tartili_isareti",
                    "kanallar_metni", "raf_omru_gun", "aktif")
    list_filter = ("kategori", "aktif", "tartili_mi", "yerel_satis",
                   "kargo_satis", "kurumsal_satis", "soguk_zincir", "abonelige_uygun")
    search_fields = ("ad", "aciklama", "mevsim")
    list_select_related = ("kategori",)
    prepopulated_fields = {"slug": ("ad",)}
    list_editable = ("aktif",)
    inlines = [MagazaUrunSatiri]
    fieldsets = (
        ("Ürün", {"fields": ("kategori", "ad", "slug", "aciklama", "gorsel", "sira", "aktif")}),
        ("Satış biçimi", {
            "description": "Tartılı üründe sepette provizyon alınır, kesin tutar tartımdan "
                           "sonra çekilir. Tartılı ürün kilogramla satılır.",
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

    # -- fiyat sütunu --------------------------------------------------------
    # Fiyat MagazaUrun'da durur, Urun'da değil; list_editable yalnızca modelin
    # kendi alanlarını kabul ettiği için kutuyu elle çiziyor, kaydı
    # changelist_view'da kendimiz yapıyoruz. Amaç: ürünü ve fiyatını tek
    # ekranda görüp girmek.

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
        # Satır başına ayrı sorgu olmasın diye fiyatı listeye tek sorguda ekliyoruz.
        qs = super().get_queryset(request)
        magaza = self.fiyat_magazasi(request)
        qs = qs.annotate(_fiyat_duzenlenebilir=Value(
            request.user.has_perm("katalog.change_magazaurun"), output_field=BooleanField()))
        if magaza is None:
            return qs.annotate(_fiyat=Value(None, output_field=DecimalField()),
                               _fiyat_magazasi=Value(None, output_field=IntegerField()))
        kayit = MagazaUrun.objects.filter(magaza=magaza, urun=OuterRef("pk"))
        return qs.annotate(_fiyat=Subquery(kayit.values("fiyat")[:1]),
                           _fiyat_magazasi=Value(magaza.pk, output_field=IntegerField()))

    @admin.display(description="fiyat")
    def fiyat_kutusu(self, nesne):
        if getattr(nesne, "_fiyat_magazasi", None) is None:
            return "—"
        birim = "kg" if nesne.birim == Birim.KILOGRAM else nesne.birim_metni.lower()
        deger = fiyat_yaz(nesne._fiyat) if nesne._fiyat is not None else ""
        if not nesne._fiyat_duzenlenebilir:
            return f"{deger} ₺ / {birim}" if deger else "—"
        return format_html(
            '<input type="text" name="fiyat_{}" value="{}" size="7" inputmode="decimal"'
            ' placeholder="fiyat" style="text-align:right"> ₺ / {}'
            '<input type="hidden" name="fiyat_ilk_{}" value="{}">',
            nesne.pk, deger, birim, nesne.pk, deger)

    def changelist_view(self, request, extra_context=None):
        if (request.method == "POST" and "_save" in request.POST
                and request.user.has_perm("katalog.change_magazaurun")):
            self.fiyatlari_kaydet(request)
        return super().changelist_view(request, extra_context)

    def fiyatlari_kaydet(self, request):
        magaza = self.fiyat_magazasi(request)
        if magaza is None:
            return
        degisen, hatalar = 0, []
        for anahtar, metin in request.POST.items():
            if not anahtar.startswith("fiyat_") or anahtar.startswith("fiyat_ilk_"):
                continue
            pk = anahtar.removeprefix("fiyat_")
            # Yalnızca değiştirilen kutular yazılır; başka biri aynı anda
            # "Mağaza ürünleri"nden fiyat girdiyse üzerine basmayalım.
            if not pk.isdigit() or metin.strip() == request.POST.get(f"fiyat_ilk_{pk}", "").strip():
                continue
            urun = Urun.objects.filter(pk=pk).first()
            if urun is None:
                continue
            try:
                tutar = fiyat_oku(metin)
            except ValueError:
                hatalar.append(f"{urun.ad}: “{metin}” fiyat olarak okunamadı")
                continue
            kayit, _ = MagazaUrun.objects.get_or_create(magaza=magaza, urun=urun)
            kayit.fiyat = tutar
            try:
                kayit.full_clean()
            except ValidationError as hata:
                hatalar.append(f"{urun.ad}: " + " ".join(
                    m for mesajlar in hata.message_dict.values() for m in mesajlar))
                continue
            kayit.save()
            degisen += 1
        if degisen:
            self.message_user(request, f"{degisen} ürünün fiyatı kaydedildi ({magaza.ad}).")
        for hata in hatalar:
            self.message_user(request, f"Kaydedilmedi — {hata}", level=messages.ERROR)

    @admin.display(description="satış")
    def satis_bilgisi(self, nesne):
        return nesne.satis_adimi_metni

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


@admin.register(MagazaUrun)
class MagazaUrunAdmin(MagazaKisitliAdmin, admin.ModelAdmin):
    magaza_yolu = "magaza"

    list_display = ("urun_adi", "kategori_adi", "birim_adi", "fiyat",
                    "fiyat_gosterim", "durum", "aktif", "magaza")
    list_editable = ("fiyat", "durum", "aktif")
    list_filter = ("magaza", "aktif", "durum", "urun__kategori", "urun__tartili_mi")
    search_fields = ("urun__ad", "urun__kategori__ad")
    list_select_related = ("urun", "urun__kategori", "magaza")
    autocomplete_fields = ("urun",)
    list_per_page = 60
    fieldsets = (
        (None, {"fields": ("magaza", "urun")}),
        ("Fiyat", {"fields": (("fiyat", "eski_fiyat"),)}),
        ("Satış", {"fields": ("durum", "aktif", "gunluk_limit", "sira")}),
    )
    actions = ["satisa_ac", "satisi_kapat", "tukendi_isaretle"]

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
        metin = f"{nesne.fiyat:,.2f}".replace(",", "#").replace(".", ",").replace("#", ".")
        if nesne.indirimli_mi:
            eski = f"{nesne.eski_fiyat:,.2f}".replace(",", "#").replace(".", ",").replace("#", ".")
            return format_html(
                '<s style="color:#8A8A8A">{} ₺</s> <b style="color:#1F5132">{} ₺</b>'
                ' <span style="color:#D98A2B">%{}</span>',
                eski, metin, nesne.indirim_orani)
        return format_html("<b>{} ₺</b>", metin)

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
