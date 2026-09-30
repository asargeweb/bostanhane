"""
Bostanhane — yönetim paneli kayıtları

Bu dosya `core/admin.py` yerine geçer.
Django'nun hazır yönetim paneli, kendi panellerimizi yazana kadar
veri girmek ve kontrol etmek için fazlasıyla yeterli.
"""

from django.contrib import admin
from django.utils import timezone
from .models import Magaza, Mahalle, HaftalikTeslimGunu, TeslimTakvimi


class HaftalikTeslimGunuSatiri(admin.TabularInline):
    model = HaftalikTeslimGunu
    extra = 1
    fields = ("gun", "teslim_baslangic", "teslim_bitis", "kesim_gun_farki",
              "kesim_saati", "kapasite", "aktif")


class MahalleSatiri(admin.TabularInline):
    model = Mahalle
    extra = 0
    fields = ("ad", "slug", "gunluk_kapasite", "sira", "aktif")
    prepopulated_fields = {"slug": ("ad",)}
    show_change_link = True


@admin.register(Magaza)
class MagazaAdmin(admin.ModelAdmin):
    list_display = ("ad", "il", "ilce", "mahalle_sayisi", "aktif")
    list_filter = ("aktif", "il")
    search_fields = ("ad", "il", "ilce")
    prepopulated_fields = {"slug": ("ad",)}
    inlines = [MahalleSatiri]
    fieldsets = (
        ("Mağaza", {"fields": ("ad", "slug", "aktif")}),
        ("Konum", {"fields": ("il", "ilce", "adres", ("enlem", "boylam"))}),
        ("İletişim", {"fields": ("telefon", "eposta")}),
    )

    @admin.display(description="mahalle")
    def mahalle_sayisi(self, obj):
        return obj.mahalleler.count()


@admin.register(Mahalle)
class MahalleAdmin(admin.ModelAdmin):
    list_display = ("ad", "magaza", "teslim_gunleri_metni", "gunluk_kapasite", "aktif")
    list_filter = ("magaza", "aktif")
    search_fields = ("ad",)
    prepopulated_fields = {"slug": ("ad",)}
    inlines = [HaftalikTeslimGunuSatiri]
    actions = ["takvim_uret"]

    @admin.action(description="Seçili mahalleler için 8 haftalık takvim üret")
    def takvim_uret(self, request, queryset):
        toplam = 0
        for mahalle in queryset:
            for kural in mahalle.haftalik_gunler.filter(aktif=True):
                toplam += len(TeslimTakvimi.kural_uret(kural))
        if toplam:
            self.message_user(request, f"{toplam} yeni teslim günü takvime eklendi.")
        else:
            self.message_user(request, "Yeni kayıt eklenmedi; takvim zaten dolu görünüyor.")


@admin.register(HaftalikTeslimGunu)
class HaftalikTeslimGunuAdmin(admin.ModelAdmin):
    list_display = ("mahalle", "gun", "kesim_saati", "teslim_baslangic", "teslim_bitis", "aktif")
    list_filter = ("gun", "aktif", "mahalle__magaza")
    search_fields = ("mahalle__ad",)


@admin.register(TeslimTakvimi)
class TeslimTakvimiAdmin(admin.ModelAdmin):
    list_display = ("tarih", "mahalle", "durum", "kapasite", "kesim_zamani", "durum_rozeti")
    list_filter = ("durum", "mahalle__magaza", "mahalle")
    date_hierarchy = "tarih"
    search_fields = ("mahalle__ad",)
    actions = ["kes"]

    @admin.display(description="sipariş")
    def durum_rozeti(self, obj):
        if obj.siparis_alinabilir:
            kalan = obj.kesime_kalan
            saat = int(kalan.total_seconds() // 3600)
            return f"Açık · kesime {saat} saat"
        if obj.durum == TeslimTakvimi.Durum.ACIK:
            return "Kesim saati geçti"
        return obj.get_durum_display()

    @admin.action(description="Seçili günleri kes (sipariş almayı kapat)")
    def kes(self, request, queryset):
        adet = queryset.filter(durum=TeslimTakvimi.Durum.ACIK).update(
            durum=TeslimTakvimi.Durum.KESILDI, guncellendi=timezone.now()
        )
        self.message_user(request, f"{adet} teslim günü kesildi.")


admin.site.site_header = "Bostanhane Yönetimi"
admin.site.site_title = "Bostanhane"
admin.site.index_title = "Yönetim paneli"


from .models import IlgiKaydi  # noqa: E402


@admin.register(IlgiKaydi)
class IlgiKaydiAdmin(admin.ModelAdmin):
    list_display = ("eposta", "mahalle_adi", "telefon", "olusturuldu", "haber_verildi")
    list_filter = ("haber_verildi", "olusturuldu")
    search_fields = ("eposta", "telefon", "mahalle_adi")
    list_editable = ("haber_verildi",)
    date_hierarchy = "olusturuldu"
