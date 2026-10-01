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

from django.contrib import admin
from django.utils.html import format_html

from core.admin_araclar import MagazaKisitliAdmin

from .models import Kategori, MagazaUrun, Urun


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


@admin.register(Urun)
class UrunAdmin(admin.ModelAdmin):
    list_display = ("ad", "kategori", "satis_bilgisi", "tartili_isareti",
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
