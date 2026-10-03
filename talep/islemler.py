"""
Bostanhane — talep işlemleri

Bu dosya `talep/islemler.py` olarak kaydedilir.

İki işlev var: talebi açmak ve karara bağlamak. İkisi de görünümlerden ve
panelden çağrılır; kuralların tek yerde durması için.

**Karar verirken para iade ediliyor.** Bu yüzden karar bir model alanı
değiştirmekten ibaret değil: `odeme.islemler.iade_et` çağrılıyor, sağlayıcıya
istek gidiyor, deftere yazılıyor. İade başarısızsa talep karara bağlanmıyor —
"kabul edildi" yazıp parayı göndermemek, hiç karar vermemekten kötü.
"""

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from core.araclar import para_yaz
from odeme.islemler import iade_et

from .models import Talep

SIFIR = Decimal("0.00")


@transaction.atomic
def talep_ac(siparis, kullanici, tur, aciklama, kalem=None):
    """
    Müşteri adına talep açar.

    Aynı kalem için açık bir talep varsa ikincisi açılmıyor — müşteri iki kez
    "Bildir"e basınca mağaza aynı şikâyeti iki kez görmesin.
    """
    uygun, sebep = Talep.acilabilir_mi(siparis)
    if not uygun:
        raise ValidationError(sebep)

    var = siparis.talepler.filter(
        kalem=kalem, durum__in=[Talep.Durum.ACIK, Talep.Durum.INCELENIYOR]).first()
    if var is not None:
        return var

    talep = Talep(siparis=siparis, kalem=kalem, tur=tur,
                  aciklama=(aciklama or "").strip())
    talep.full_clean()
    talep.save()
    return talep


@transaction.atomic
def karara_bagla(talep, durum, kullanici, karar_notu, iade_tutari=None):
    """
    Mağaza yöneticisinin kararını işler; gerekiyorsa parayı iade eder.

    `durum` kabul ya da kısmi ise `iade_tutari` zorunlu ve sıfırdan büyük olmalı.
    Red kararında iade yapılmaz.

    Sıra önemli: **önce para gider, sonra talep kapanır.** İade başarısız olursa
    hata fırlatılıyor ve işlem geri alınıyor; talep açık kalıyor. Böylece
    "kabul edildi ama para gitmedi" durumu oluşmuyor.
    """
    if talep.karara_baglandi_mi:
        raise ValidationError("Bu talep zaten karara bağlanmış.")
    if durum not in (Talep.Durum.KABUL, Talep.Durum.KISMI, Talep.Durum.RED):
        raise ValidationError("Karar kabul, kısmi kabul ya da red olmalı.")

    karar_notu = (karar_notu or "").strip()
    if not karar_notu:
        raise ValidationError({"karar_notu": "Müşteriye bir açıklama yazın."})

    tutar = SIFIR
    if durum in (Talep.Durum.KABUL, Talep.Durum.KISMI):
        tutar = Decimal(str(iade_tutari or 0))
        if tutar <= SIFIR:
            raise ValidationError(
                {"iade_tutari": "Kabul kararında iade tutarı sıfırdan büyük olmalı."})
        if tutar > talep.en_fazla_iade:
            raise ValidationError(
                {"iade_tutari": f"En fazla {para_yaz(talep.en_fazla_iade)} iade edilebilir."})

        islem = iade_et(talep.siparis, tutar, kullanici=kullanici,
                        sebep=f"Talep #{talep.pk} · {talep.get_tur_display()}")
        if not islem.basarili_mi:
            # Para gitmediyse talebi kapatmıyoruz; mağaza tekrar deneyebilsin.
            raise ValidationError(
                f"İade yapılamadı: {islem.hata_mesaji or 'sağlayıcı reddetti'}. "
                f"Talep açık bırakıldı.")

    talep.durum = durum
    talep.iade_tutari = tutar
    talep.karar_notu = karar_notu
    talep.karar_veren = kullanici
    talep.karar_zamani = timezone.now()
    talep.save(update_fields=["durum", "iade_tutari", "karar_notu", "karar_veren",
                              "karar_zamani", "guncellendi"])
    return talep


def acik_talebi_var_mi(siparis):
    """
    Otomatik teslim onayı bunu sorar: müşteri bir sorun bildirmiş mi?

    Açık talebi olan sipariş otomatik onaylanmaz — müşteri cevap vermiş
    sayılır, mağaza karar verene kadar sipariş açık kalır.
    """
    return siparis.talepler.filter(
        durum__in=[Talep.Durum.ACIK, Talep.Durum.INCELENIYOR]).exists()
