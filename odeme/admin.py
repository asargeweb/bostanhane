"""
Bostanhane — ödeme defteri paneli

Bu dosya `odeme/admin.py` olarak kaydedilir.

**Tamamen salt okunur.** Para hareketi panelden elle yazılmaz, değiştirilmez,
silinmez. Her satır sağlayıcıya gitmiş gerçek bir isteğin karşılığı; elle
düzeltilirse defter yalan söylemeye başlar.

İşlem yapmak gerekirse (iade gibi) sipariş ekranından, `odeme.islemler`
işlevleri üzerinden yapılır — o yol hem sağlayıcıya gider hem deftere yazar.
"""

from django.contrib import admin
from django.utils.html import format_html

from core.admin_araclar import MagazaKisitliAdmin
from core.araclar import para_yaz

from .models import OdemeIslemi

RENKLER = {
    OdemeIslemi.Durum.BASARILI: "#2E6B2A",
    OdemeIslemi.Durum.BASARISIZ: "#B23A24",
    OdemeIslemi.Durum.BEKLIYOR: "#8A5A12",
}


@admin.register(OdemeIslemi)
class OdemeIslemiAdmin(MagazaKisitliAdmin, admin.ModelAdmin):
    magaza_yolu = "siparis__magaza"

    list_display = ("olusturuldu", "siparis_no", "tur", "tutar_gosterim",
                    "durum_gosterim", "saglayici", "islem_no_kisa")
    list_filter = ("tur", "durum", "saglayici", "siparis__magaza", "olusturuldu")
    search_fields = ("siparis__numara", "saglayici_islem_no", "istek_anahtari",
                     "siparis__uye__ad_soyad", "siparis__uye__telefon")
    list_select_related = ("siparis", "siparis__uye", "siparis__magaza")
    date_hierarchy = "olusturuldu"
    fieldsets = (
        (None, {"fields": (("siparis", "tur", "durum"), ("tutar", "kaynak_islem"))}),
        ("Sağlayıcı", {"fields": (("saglayici", "saglayici_islem_no"), "istek_anahtari",
                                  ("hata_kodu", "hata_mesaji"), "yanit")}),
        ("Kayıt", {"fields": (("kullanici", "aciklama"), ("olusturuldu", "guncellendi"))}),
    )

    def get_readonly_fields(self, request, obj=None):
        """Bütün alanlar salt okunur — defter elle düzeltilmez."""
        return [alan.name for alan in self.model._meta.fields] + ["kaynak_islem"]

    @admin.display(description="sipariş", ordering="siparis__numara")
    def siparis_no(self, nesne):
        return nesne.siparis.numara

    @admin.display(description="tutar", ordering="tutar")
    def tutar_gosterim(self, nesne):
        # İade ve bloke çözme parayı geri veriyor; eksi işaretle gösteriyoruz
        # ki defter okunurken yön belli olsun.
        geri = nesne.tur in (OdemeIslemi.Tur.IADE, OdemeIslemi.Tur.BLOKE_COZ)
        return f"−{para_yaz(nesne.tutar)}" if geri else para_yaz(nesne.tutar)

    @admin.display(description="durum", ordering="durum")
    def durum_gosterim(self, nesne):
        return format_html('<b style="color:{}">{}</b>',
                           RENKLER.get(nesne.durum, "#5B675A"), nesne.get_durum_display())

    @admin.display(description="sağlayıcı işlem no")
    def islem_no_kisa(self, nesne):
        if not nesne.saglayici_islem_no:
            return "—"
        return format_html('<span title="{}">{}</span>',
                           nesne.saglayici_islem_no, nesne.saglayici_islem_no[-16:])

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
