"""
Teslim onayı (Adım 6c): üye "eksiksiz teslim aldım" der; cevap gelmezse belli
bir süre sonra (SatisAyarlari.otomatik_teslim_onayi_saat) sipariş onaylanmış sayılır.

Sorun bildirimi `talep` uygulamasında (Talep modeli). **Açık talebi olan sipariş
otomatik onaylanmaz:** müşteri cevap vermiş sayılır, mağaza karar verene kadar
sipariş açık kalır. Bu karar artık iç nottaki bir metne değil talep kaydına bakıyor —
iç not serbest metin, biri düzenlerken işareti silerse şikâyet kaybolurdu.
"""

from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import Siparis

# Yalnızca müşteriye "otomatik onaylandı" demek için; karar mantığı buna bakmıyor.
OTOMATIK_ISARETI = "otomatik teslim onayı"


def acik_talebi_var_mi(siparis):
    # talep, siparis'e bağlı; modül yüklenirken değil çağrılırken içeri alınıyor.
    from talep.islemler import acik_talebi_var_mi as _acik
    return _acik(siparis)


def otomatik_onaylandi_mi(siparis):
    return OTOMATIK_ISARETI in (siparis.ic_not or "")


def onay_bekliyor_mu(siparis):
    """Teslim edildi, onay yok, açık sorun bildirimi yok."""
    return (siparis.durum == Siparis.Durum.TESLIM_EDILDI and siparis.onay_zamani is None
            and not acik_talebi_var_mi(siparis))


def teslimi_onayla(siparis):
    """Üye "eksiksiz teslim aldım" dedi. İkinci kez onay verilemez."""
    if not onay_bekliyor_mu(siparis):
        raise ValidationError("Bu sipariş için teslim onayı verilemez.")
    siparis.onay_zamani = timezone.now()
    siparis.save(update_fields=["onay_zamani", "guncellendi"])


def otomatik_onaylanacaklar(simdi=None):
    """Süresi dolmuş, onaysız, açık talebi olmayan teslim edilmiş siparişler."""
    simdi = simdi or timezone.now()
    adaylar = (Siparis.objects
               .filter(durum=Siparis.Durum.TESLIM_EDILDI, onay_zamani__isnull=True,
                       teslim_zamani__isnull=False)
               .select_related("magaza"))
    # Süre mağaza başına panelden değişebilir; model özelliği onu okuyor.
    return [s for s in adaylar
            if s.otomatik_onay_zamani and s.otomatik_onay_zamani <= simdi
            and not acik_talebi_var_mi(s)]


def otomatik_onayla(siparis):
    siparis.onay_zamani = timezone.now()
    siparis.ic_not = (f"{siparis.ic_not}\n{timezone.localtime():%d.%m %H.%M} — "
                      f"{OTOMATIK_ISARETI} (süre içinde bildirim gelmedi)").strip()
    siparis.save(update_fields=["onay_zamani", "ic_not", "guncellendi"])
