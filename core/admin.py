"""
Bostanhane — yönetim paneli kayıtları

Bu dosya `core/admin.py` yerine geçer.

Panelde iki ayrı bölüm görünür:

**Coğrafya** — İller, İlçeler, Mahalleler. Resmî idari yapı; `cografya_yukle`
komutuyla dolar, elle girilmesi gerekmez. Buraya bakmanın sebebi genelde
"bu mahalle sistemde var mı" sorusudur.

**Hizmet alanı** — Mağazalar, Hizmet verilen mahalleler, Teslim günleri, Takvim.
Günlük iş burada yürür.
"""

from django.contrib import admin
from django.utils import timezone

from .admin_araclar import MagazaKisitliAdmin, tum_magazalari_gorur
from .models import (
    HaftalikTeslimGunu, HizmetMahallesi, Il, Ilce, IlgiKaydi,
    Magaza, Mahalle, TeslimTakvimi,
)

admin.site.site_header = "Bostanhane Yönetimi"
admin.site.site_title = "Bostanhane"
admin.site.index_title = "Yönetim paneli"


# ==========================================================================
# COĞRAFYA
# ==========================================================================
@admin.register(Il)
class IlAdmin(admin.ModelAdmin):
    list_display = ("plaka", "ad", "ilce_adedi", "mahalle_adedi")
    search_fields = ("ad",)
    ordering = ("plaka",)
    readonly_fields = ("slug",)

    @admin.display(description="ilçe")
    def ilce_adedi(self, nesne):
        return nesne.ilceler.count()

    @admin.display(description="mahalle")
    def mahalle_adedi(self, nesne):
        return Mahalle.objects.filter(ilce__il=nesne).count()


@admin.register(Ilce)
class IlceAdmin(admin.ModelAdmin):
    list_display = ("ad", "il", "mahalle_adedi", "hizmet_adedi")
    list_filter = ("il",)
    search_fields = ("ad", "il__ad")
    autocomplete_fields = ("il",)
    readonly_fields = ("slug",)

    @admin.display(description="mahalle")
    def mahalle_adedi(self, nesne):
        return nesne.mahalleler.count()

    @admin.display(description="hizmet verilen")
    def hizmet_adedi(self, nesne):
        return HizmetMahallesi.objects.filter(mahalle__ilce=nesne, aktif=True).count()


@admin.register(Mahalle)
class MahalleAdmin(admin.ModelAdmin):
    list_display = ("ad", "ilce", "il_adi", "tip", "posta_kodu", "hizmet_durumu")
    list_filter = ("tip", "ilce__il", "ilce")
    search_fields = ("ad", "ilce__ad", "posta_kodu")
    autocomplete_fields = ("ilce",)
    readonly_fields = ("slug",)
    list_select_related = ("ilce", "ilce__il")

    @admin.display(description="il", ordering="ilce__il__ad")
    def il_adi(self, nesne):
        return nesne.ilce.il.ad

    @admin.display(description="yerel teslimat")
    def hizmet_durumu(self, nesne):
        hizmet = nesne.yerel_hizmet()
        return hizmet.magaza.ad if hizmet else "—"


# ==========================================================================
# HİZMET ALANI
# ==========================================================================
class HizmetMahallesiSatiri(admin.TabularInline):
    model = HizmetMahallesi
    extra = 0
    fields = ("mahalle", "gunluk_kapasite", "sira", "aktif")
    autocomplete_fields = ("mahalle",)
    show_change_link = True
    verbose_name = "hizmet verilen mahalle"
    verbose_name_plural = "hizmet verilen mahalleler"


@admin.register(Magaza)
class MagazaAdmin(MagazaKisitliAdmin, admin.ModelAdmin):
    magaza_yolu = "pk"

    list_display = ("ad", "ilce", "il", "hizmet_adedi", "aktif")
    list_filter = ("aktif", "il")
    search_fields = ("ad", "il__ad", "ilce__ad")
    prepopulated_fields = {"slug": ("ad",)}
    autocomplete_fields = ("il", "ilce")
    inlines = [HizmetMahallesiSatiri]
    fieldsets = (
        ("Mağaza", {"fields": ("ad", "slug", "aktif")}),
        ("Konum", {"fields": (("il", "ilce"), "adres", ("enlem", "boylam"))}),
        ("İletişim", {"fields": ("telefon", "eposta")}),
    )

    @admin.display(description="hizmet verilen mahalle")
    def hizmet_adedi(self, nesne):
        return nesne.hizmet_mahalleleri.filter(aktif=True).count()


class HaftalikTeslimGunuSatiri(admin.TabularInline):
    model = HaftalikTeslimGunu
    extra = 1
    fields = ("gun", "teslim_baslangic", "teslim_bitis", "kesim_gun_farki",
              "kesim_saati", "kapasite", "aktif")


@admin.register(HizmetMahallesi)
class HizmetMahallesiAdmin(MagazaKisitliAdmin, admin.ModelAdmin):
    magaza_yolu = "magaza"
    suzulecek_modeller = ("magaza", "mahalle")

    list_display = ("mahalle", "magaza", "teslim_gunleri_metni", "gunluk_kapasite", "sira", "aktif")
    list_filter = ("magaza", "aktif", "mahalle__ilce")
    search_fields = ("mahalle__ad",)
    autocomplete_fields = ("mahalle",)
    list_select_related = ("mahalle", "magaza")
    list_editable = ("sira", "aktif")
    inlines = [HaftalikTeslimGunuSatiri]
    actions = ["takvim_uret"]

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """
        Mağaza yöneticisi mahalle seçerken kendi ilinin mahalleleri görünsün.
        İlçe sınırı koymuyoruz: bir mağaza komşu ilçeye de hizmet verebilir.
        """
        if db_field.name == "mahalle" and not self.tum_magazalari_gorur(request):
            magaza = self.kullanicinin_magazasi(request)
            if magaza is not None:
                kwargs["queryset"] = Mahalle.objects.filter(ilce__il=magaza.il)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    @admin.action(description="Seçili mahalleler için 8 haftalık takvim üret")
    def takvim_uret(self, request, queryset):
        toplam = 0
        for hizmet in queryset:
            for kural in hizmet.haftalik_gunler.filter(aktif=True):
                toplam += len(TeslimTakvimi.kural_uret(kural))
        if toplam:
            self.message_user(request, f"{toplam} yeni teslim günü takvime eklendi.")
        else:
            self.message_user(request, "Yeni kayıt eklenmedi; takvim zaten dolu görünüyor.")


@admin.register(HaftalikTeslimGunu)
class HaftalikTeslimGunuAdmin(MagazaKisitliAdmin, admin.ModelAdmin):
    magaza_yolu = "hizmet_mahallesi__magaza"

    list_display = ("hizmet_mahallesi", "gun", "kesim_saati",
                    "teslim_baslangic", "teslim_bitis", "aktif")
    list_filter = ("gun", "aktif", "hizmet_mahallesi__magaza")
    search_fields = ("hizmet_mahallesi__mahalle__ad",)
    list_select_related = ("hizmet_mahallesi", "hizmet_mahallesi__mahalle")


@admin.register(TeslimTakvimi)
class TeslimTakvimiAdmin(MagazaKisitliAdmin, admin.ModelAdmin):
    magaza_yolu = "hizmet_mahallesi__magaza"

    list_display = ("tarih", "hizmet_mahallesi", "durum", "kapasite",
                    "kesim_zamani", "durum_rozeti")
    list_filter = ("durum", "hizmet_mahallesi__magaza", "hizmet_mahallesi")
    date_hierarchy = "tarih"
    search_fields = ("hizmet_mahallesi__mahalle__ad",)
    list_select_related = ("hizmet_mahallesi", "hizmet_mahallesi__mahalle")
    actions = ["kes"]

    @admin.display(description="sipariş")
    def durum_rozeti(self, nesne):
        if nesne.siparis_alinabilir:
            kalan = nesne.kesime_kalan
            saat = int(kalan.total_seconds() // 3600)
            return f"Açık · kesime {saat} saat"
        if nesne.durum == TeslimTakvimi.Durum.ACIK:
            return "Kesim saati geçti"
        return nesne.get_durum_display()

    @admin.action(description="Seçili günleri kes (sipariş almayı kapat)")
    def kes(self, request, queryset):
        adet = queryset.filter(durum=TeslimTakvimi.Durum.ACIK).update(
            durum=TeslimTakvimi.Durum.KESILDI, guncellendi=timezone.now()
        )
        self.message_user(request, f"{adet} teslim günü kesildi.")


@admin.register(IlgiKaydi)
class IlgiKaydiAdmin(admin.ModelAdmin):
    """
    İlgi kayıtları hiçbir mağazaya bağlı değil (ziyaretçi mahalle adını serbest
    yazıyor). Mağazaya göre süzemediğimiz için yalnızca süper admin görür;
    aksi halde her mağaza yöneticisi bütün şehirlerin e-postalarını görürdü.
    """

    list_display = ("eposta", "mahalle_adi", "telefon", "olusturuldu", "haber_verildi")
    list_filter = ("haber_verildi", "olusturuldu")
    search_fields = ("eposta", "telefon", "mahalle_adi")
    list_editable = ("haber_verildi",)
    date_hierarchy = "olusturuldu"

    def has_module_permission(self, request):
        return tum_magazalari_gorur(request)

    def has_view_permission(self, request, obj=None):
        return tum_magazalari_gorur(request)

    def has_change_permission(self, request, obj=None):
        return tum_magazalari_gorur(request)

    def has_delete_permission(self, request, obj=None):
        return tum_magazalari_gorur(request)
