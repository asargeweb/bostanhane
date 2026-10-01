"""
Bostanhane — sipariş yönetim paneli

Bu dosya `siparis/admin.py` yerine geçer.

Panelde iki liste var:

**Siparişler** — günlük iş. Mağaza yöneticisi buradan siparişi görür, durumunu
ilerletir, tartım sonrası tutarı kontrol eder.

**Sepetler** — yalnızca okunur. "Müşteri sepete ekledi ama sipariş vermedi" durumunu
görmek için; terk edilen sepet, fiyatın mı yoksa kesim saatinin mi engellediğini
anlamaya yarar.

Paketleme ve kurye ekranları ayrı yazılacak (Adım 6); burası yönetici gözü.
"""

from django.contrib import admin
from django.utils.html import format_html, format_html_join
from django.utils.safestring import mark_safe

from core.admin_araclar import MagazaKisitliAdmin
from core.araclar import para_yaz as para   # 42,90 ₺ — tek biçimleyici, core/araclar.py'de

from .models import Sepet, SepetKalemi, Siparis, SiparisKalemi


# ==========================================================================
# SEPET
# ==========================================================================
class SepetKalemiSatiri(admin.TabularInline):
    model = SepetKalemi
    extra = 0
    fields = ("magaza_urun", "miktar", "tutar_gosterim")
    readonly_fields = ("magaza_urun", "miktar", "tutar_gosterim")
    can_delete = False

    @admin.display(description="tutar")
    def tutar_gosterim(self, nesne):
        return para(nesne.tutar)

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Sepet)
class SepetAdmin(MagazaKisitliAdmin, admin.ModelAdmin):
    magaza_yolu = "magaza"

    list_display = ("sahip", "magaza", "kalem_adedi", "ara_toplam_gosterim",
                    "teslim_takvimi", "guncellendi")
    list_filter = ("magaza", "teslim_takvimi__tarih")
    search_fields = ("uye__ad_soyad", "uye__telefon")
    list_select_related = ("uye", "magaza", "teslim_takvimi")
    inlines = [SepetKalemiSatiri]
    readonly_fields = ("uye", "oturum_anahtari", "magaza", "teslim_takvimi", "adres",
                       "ara_toplam_gosterim", "olusturuldu", "guncellendi")

    @admin.display(description="sahibi", ordering="uye__ad_soyad")
    def sahip(self, nesne):
        return nesne.uye.ad_soyad if nesne.uye else "ziyaretçi"

    @admin.display(description="ürün")
    def kalem_adedi(self, nesne):
        return nesne.kalem_sayisi

    @admin.display(description="ara toplam")
    def ara_toplam_gosterim(self, nesne):
        return para(nesne.ara_toplam)

    def has_add_permission(self, request):
        return False


# ==========================================================================
# SİPARİŞ
# ==========================================================================
class SiparisKalemiSatiri(admin.TabularInline):
    """
    Tartım burada girilir. `teslim_miktari` dışındaki alanlar dondurulmuş
    bilgidir — sipariş anındaki ad ve fiyat; değiştirilmemeli.
    """
    model = SiparisKalemi
    extra = 0
    fields = ("urun_adi", "birim_adi", "birim_fiyat_gosterim", "siparis_miktari",
              "teslim_miktari", "durum", "tutar_gosterim", "not_metni")
    readonly_fields = ("urun_adi", "birim_adi", "birim_fiyat_gosterim",
                       "siparis_miktari", "tutar_gosterim")
    can_delete = False

    @admin.display(description="birim fiyat")
    def birim_fiyat_gosterim(self, nesne):
        return para(nesne.birim_fiyat)

    @admin.display(description="tutar")
    def tutar_gosterim(self, nesne):
        if nesne.bulunamadi_mi:
            return format_html('<b style="color:#B23A24">{}</b>', "bulunamadı · 0,00 ₺")
        if nesne.eksik_mi:
            return format_html('<span title="{}">{} <small style="color:#8A5A12">({})</small></span>',
                               "tartı farkı", para(nesne.tutar), para(nesne.fark_tutari))
        return para(nesne.tutar)

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Siparis)
class SiparisAdmin(MagazaKisitliAdmin, admin.ModelAdmin):
    magaza_yolu = "magaza"

    list_display = ("numara", "uye_adi", "teslim_bilgisi", "kalem_adedi",
                    "toplam_gosterim", "durum", "odeme_durumu", "deneme")
    list_filter = ("durum", "odeme_durumu", "kanal", "test_siparisi",
                   "magaza", "teslim_takvimi__tarih")
    search_fields = ("numara", "uye__ad_soyad", "uye__telefon", "teslim_acik_adres")
    list_select_related = ("uye", "magaza", "teslim_takvimi",
                           "teslim_takvimi__hizmet_mahallesi__mahalle")
    date_hierarchy = "olusturuldu"
    inlines = [SiparisKalemiSatiri]
    readonly_fields = ("numara", "uye", "magaza", "teslim_takvimi", "kanal",
                       "ara_toplam", "teslimat_ucreti", "toplam", "provizyon_tutari",
                       "test_siparisi", "ozet_kutusu",
                       "kesildi_zamani", "hazirlandi_zamani", "teslim_zamani",
                       "onay_zamani", "olusturuldu", "guncellendi")
    fieldsets = (
        (None, {"fields": ("numara", "ozet_kutusu")}),
        ("Sipariş", {"fields": (("uye", "magaza"), ("teslim_takvimi", "kanal"),
                                ("durum", "odeme_durumu"))}),
        ("Teslimat adresi", {
            "description": "Bu bilgiler sipariş anında kopyalandı; müşteri adresini "
                           "sonradan değiştirse bile sipariş olduğu gibi kalır.",
            "fields": (("teslim_ad_soyad", "teslim_telefon"), "teslim_acik_adres",
                       ("teslim_mahalle", "teslim_ilce", "teslim_il"), "teslim_tarif",
                       ("teslim_enlem", "teslim_boylam")),
        }),
        ("Tutarlar", {"fields": (("ara_toplam", "teslimat_ucreti", "toplam"),
                                 ("provizyon_tutari", "cekilen_tutar"))}),
        ("Notlar", {"fields": ("musteri_notu", "ic_not")}),
        ("Zaman", {"classes": ("collapse",),
                   "fields": (("kesildi_zamani", "hazirlandi_zamani"),
                              ("teslim_zamani", "onay_zamani"),
                              ("olusturuldu", "guncellendi"))}),
    )
    actions = ["hazirlandi_isaretle", "yola_cikti_isaretle", "teslim_edildi_isaretle"]

    # -- sütunlar ----------------------------------------------------------
    @admin.display(description="üye", ordering="uye__ad_soyad")
    def uye_adi(self, nesne):
        return nesne.uye.ad_soyad

    @admin.display(description="teslimat", ordering="teslim_takvimi__tarih")
    def teslim_bilgisi(self, nesne):
        if nesne.teslim_takvimi is None:
            return "Kargo"
        t = nesne.teslim_takvimi
        return f"{t.tarih:%d.%m} · {t.hizmet_mahallesi.mahalle.ad}"

    @admin.display(description="ürün")
    def kalem_adedi(self, nesne):
        return nesne.kalemler.count()

    @admin.display(description="toplam", ordering="toplam")
    def toplam_gosterim(self, nesne):
        return para(nesne.toplam)

    @admin.display(description="deneme", boolean=True, ordering="test_siparisi")
    def deneme(self, nesne):
        return nesne.test_siparisi

    @admin.display(description="özet")
    def ozet_kutusu(self, nesne):
        """Siparişin önemli üç sayısını bir arada gösterir."""
        if nesne.pk is None:
            return "—"
        # Her satır format_html ile kuruluyor: ürün adı müşteriden/panelden gelen
        # metin, doğrudan HTML'e gömülmemeli.
        satirlar = [
            format_html("Bloke edilen: <b>{}</b>", para(nesne.provizyon_tutari)),
            format_html("Çekilecek: <b>{}</b>", para(nesne.toplam)),
        ]
        eksik = nesne.eksik_kalemler
        if eksik:
            satirlar.append(format_html(
                '<span style="color:#8A5A12">Eksik/bulunamayan: {}</span>',
                ", ".join(k.urun_adi for k in eksik)))
        if nesne.test_siparisi:
            satirlar.append(format_html(
                '<span style="color:#D98A2B"><b>{}</b> — {}</span>',
                "DENEME SİPARİŞİ",
                "vitrin test modundayken verildi, raporlara girmez"))
        return format_html_join(mark_safe("<br>"), "{}", ((s,) for s in satirlar))

    # -- işlemler ----------------------------------------------------------
    @admin.action(description="Hazırlandı olarak işaretle")
    def hazirlandi_isaretle(self, request, queryset):
        from django.utils import timezone
        adet = queryset.exclude(durum=Siparis.Durum.IPTAL).update(
            durum=Siparis.Durum.HAZIRLANIYOR, hazirlandi_zamani=timezone.now())
        self.message_user(request, f"{adet} sipariş hazırlandı olarak işaretlendi.")

    @admin.action(description="Yola çıktı olarak işaretle")
    def yola_cikti_isaretle(self, request, queryset):
        adet = queryset.exclude(durum=Siparis.Durum.IPTAL).update(durum=Siparis.Durum.YOLDA)
        self.message_user(request, f"{adet} sipariş yola çıktı.")

    @admin.action(description="Teslim edildi olarak işaretle")
    def teslim_edildi_isaretle(self, request, queryset):
        adet = 0
        for siparis in queryset.exclude(durum=Siparis.Durum.IPTAL):
            siparis.teslim_edildi_isaretle()
            adet += 1
        self.message_user(request, f"{adet} sipariş teslim edildi olarak işaretlendi.")

    def has_add_permission(self, request):
        """Sipariş panelden açılmaz; müşteri verir."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Sipariş silinmez, iptal edilir — geçmiş kaybolmasın."""
        return False
