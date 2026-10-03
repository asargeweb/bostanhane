"""
Teslim onayı (Adım 6c): üye "eksiksiz teslim aldım" der ya da sorun bildirir;
cevap gelmezse belli bir süre sonra (SatisAyarlari.otomatik_teslim_onayi_saat)
sipariş onaylanmış sayılır.

Sipariş modeline dokunmadan: onay `Siparis.onay_zamani`'na, sorun bildirimi ve
otomatik onay notu `ic_not`'a yazılıyor. Sorun bildirimi için ayrı alan / model
`talep` uygulamasıyla gelecek (fotoğraflı iade talebi); o gelene kadar iç nottaki
sabit işaret kullanılıyor. Görünüm ve otomatik onay komutu aynı kuralı buradan okur.
"""

from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import Siparis

SORUN_ISARETI = "MÜŞTERİ SORUN BİLDİRDİ"
OTOMATIK_ISARETI = "otomatik teslim onayı"


def _not_ekle(siparis, satir):
    siparis.ic_not = f"{siparis.ic_not}\n{satir}".strip()


def sorun_bildirildi_mi(siparis):
    return SORUN_ISARETI in (siparis.ic_not or "")


def otomatik_onaylandi_mi(siparis):
    return OTOMATIK_ISARETI in (siparis.ic_not or "")


def onay_bekliyor_mu(siparis):
    """Teslim edildi, onay yok, sorun bildirilmedi."""
    return (siparis.durum == Siparis.Durum.TESLIM_EDILDI and siparis.onay_zamani is None
            and not sorun_bildirildi_mi(siparis))


def teslimi_onayla(siparis):
    """Üye "eksiksiz teslim aldım" dedi. İkinci kez onay verilemez."""
    if not onay_bekliyor_mu(siparis):
        raise ValidationError("Bu sipariş için teslim onayı verilemez.")
    siparis.onay_zamani = timezone.now()
    siparis.save(update_fields=["onay_zamani", "guncellendi"])


def sorun_bildir(siparis, aciklama):
    """
    Üye bir sorun bildirdi. Otomatik onay bu siparişe dokunmaz: sorun bildiren
    üye cevap vermiş sayılır, mağaza karar verene kadar sipariş açık kalır.
    """
    if not onay_bekliyor_mu(siparis):
        raise ValidationError("Bu sipariş için sorun bildirilemez.")
    aciklama = " ".join((aciklama or "").split())[:500] or "(açıklama yazılmadı)"
    _not_ekle(siparis, f"{timezone.localtime():%d.%m %H.%M} — {SORUN_ISARETI}: {aciklama}")
    siparis.save(update_fields=["ic_not", "guncellendi"])


def otomatik_onaylanacaklar(simdi=None):
    """Süresi dolmuş, onaysız, sorunsuz teslim edilmiş siparişler."""
    simdi = simdi or timezone.now()
    adaylar = (Siparis.objects
               .filter(durum=Siparis.Durum.TESLIM_EDILDI, onay_zamani__isnull=True,
                       teslim_zamani__isnull=False)
               .exclude(ic_not__contains=SORUN_ISARETI)
               .select_related("magaza"))
    # Süre mağaza başına panelden değişebilir; model özelliği onu okuyor.
    return [s for s in adaylar if s.otomatik_onay_zamani and s.otomatik_onay_zamani <= simdi]


def otomatik_onayla(siparis):
    siparis.onay_zamani = timezone.now()
    _not_ekle(siparis, f"{timezone.localtime():%d.%m %H.%M} — {OTOMATIK_ISARETI} "
                       f"(süre içinde bildirim gelmedi)")
    siparis.save(update_fields=["onay_zamani", "ic_not", "guncellendi"])
