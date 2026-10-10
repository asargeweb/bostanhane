"""
Bostanhane — bildirim defteri paneli

Bu dosya `bildirim/admin.py` olarak kaydedilir.

**Salt okunur.** Gönderilmiş mesaj panelden değiştirilmez; defter neyin gittiğini
tutar, ne gitmesi gerektiğini değil.

Listede **parça sayısı** sütunu var: bir SMS'in kaç mesaj olarak faturalandığını
gösteriyor. Metinler uzadıkça maliyet sessizce iki katına çıkabiliyor; burada
görünüyor.
"""

from django.contrib import admin
from django.utils.html import format_html

from core.admin_araclar import MagazaKisitliAdmin

from .models import Bildirim

DURUM_RENKLERI = {
    Bildirim.Durum.GONDERILDI: "#2E6B2A",
    Bildirim.Durum.BASARISIZ: "#B23A24",
    Bildirim.Durum.BEKLIYOR: "#8A5A12",
    Bildirim.Durum.ATLANDI: "#5B675A",
}


@admin.register(Bildirim)
class BildirimAdmin(MagazaKisitliAdmin, admin.ModelAdmin):
    magaza_yolu = "siparis__magaza"

    list_display = ("olusturuldu", "tur", "kanal", "adres", "siparis_no",
                    "durum_gosterim", "parca_gosterim", "kisa_metin")
    list_filter = ("durum", "kanal", "tur", "siparis__magaza", "olusturuldu")
    search_fields = ("adres", "metin", "siparis__numara", "saglayici_mesaj_no",
                     "alici__ad_soyad")
    list_select_related = ("siparis", "alici")
    date_hierarchy = "olusturuldu"
    fieldsets = (
        (None, {"fields": (("tur", "kanal", "durum"), ("alici", "siparis"))}),
        ("Gönderim", {"fields": ("adres", "konu", "metin", "olcum")}),
        ("Sağlayıcı", {"fields": (("saglayici", "saglayici_mesaj_no"),
                                  "hata_mesaji", "istek_anahtari")}),
        ("Zaman", {"fields": (("gonderim_zamani", "olusturuldu", "guncellendi"),)}),
    )

    def get_readonly_fields(self, request, obj=None):
        return [alan.name for alan in self.model._meta.fields] + ["olcum"]

    @admin.display(description="sipariş", ordering="siparis__numara")
    def siparis_no(self, nesne):
        return nesne.siparis.numara if nesne.siparis_id else "—"

    @admin.display(description="durum", ordering="durum")
    def durum_gosterim(self, nesne):
        return format_html('<b style="color:{}">{}</b>',
                           DURUM_RENKLERI.get(nesne.durum, "#5B675A"),
                           nesne.get_durum_display())

    @admin.display(description="parça")
    def parca_gosterim(self, nesne):
        """SMS kaç parça — yani kaç mesaj ücreti."""
        adet = nesne.parca_sayisi
        if adet is None:
            return "—"
        if adet > 1:
            return format_html('<b style="color:#8A5A12">{} parça</b>', adet)
        return "1"

    @admin.display(description="metin")
    def kisa_metin(self, nesne):
        metin = nesne.metin or ""
        return metin if len(metin) <= 60 else metin[:57] + "…"

    @admin.display(description="ölçüm")
    def olcum(self, nesne):
        """Metnin uzunluğu, alfabesi ve kaç parça ettiği — maliyet burada görünüyor."""
        if nesne.kanal != Bildirim.Kanal.SMS:
            return "—"
        adet = nesne.parca_sayisi
        return format_html(
            "{} karakter · {} · <b>{} parça</b>{}",
            len(nesne.metin or ""), nesne.alfabe, adet,
            " — metin kısaltılırsa tek parçaya iner" if adet > 1 else "")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
