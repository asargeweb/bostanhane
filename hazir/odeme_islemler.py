"""
Bostanhane — ödeme işlemleri

Bu dosya `odeme/islemler.py` olarak kaydedilir.

Dışarıdan çağrılacak dört işlev burada. Görünümler ve komutlar sağlayıcıyı
doğrudan çağırmaz, buradan geçer — çünkü her para hareketinin deftere
yazılması, siparişin durumunun güncellenmesi ve aynı isteğin iki kez
gitmemesi burada garanti ediliyor.

### Akış

```
sipariş onaylandı        →  provizyon_al()      bloke edilir, para çekilmez
   (tartım yapılır, kesin tutar belli olur)
sipariş hazırlandı       →  cekim_yap()         yalnızca kesin tutar çekilir
sipariş iptal edildi     →  bloke_coz()         bloke serbest bırakılır
kusurlu ürün bildirimi   →  iade_et()           çekilmiş paradan iade
```

### Çift çekim koruması

Her işlevin bir **istek anahtarı** var: `<sipariş no>-<tür>-<sıra>`. Aynı
anahtarla ikinci kez çağrılırsa yeni istek gönderilmez, var olan kayıt döner.
Ağ koptuğunda, kullanıcı iki kez tıkladığında ya da zamanlanmış görev iki kez
tetiklendiğinde müşteriden iki kez para çekilmez.
"""

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from core.araclar import para_yaz
from siparis.models import Siparis

from .models import OdemeIslemi
from .saglayicilar import saglayici_sec

SIFIR = Decimal("0.00")


def _anahtar(siparis, tur, sira=1):
    return f"{siparis.numara}-{tur}-{sira}"


def _var_olan(anahtar):
    return OdemeIslemi.objects.filter(istek_anahtari=anahtar).first()


def _basarili_islem(siparis, tur):
    return siparis.odeme_islemleri.filter(
        tur=tur, durum=OdemeIslemi.Durum.BASARILI).first()


# ==========================================================================
# PROVİZYON
# ==========================================================================
@transaction.atomic
def provizyon_al(siparis, kullanici=None, tutar=None):
    """
    Karttan tutarı bloke eder. Para çekilmez.

    Sipariş onaylandığı anda çağrılır. Tutar verilmezse siparişin
    `provizyon_tutari` alanı kullanılır (tahmini tutar + tampon).
    """
    tutar = Decimal(str(tutar)) if tutar is not None else siparis.provizyon_tutari
    if tutar <= SIFIR:
        raise ValidationError("Provizyon tutarı sıfırdan büyük olmalı.")

    anahtar = _anahtar(siparis, OdemeIslemi.Tur.PROVIZYON)
    var = _var_olan(anahtar)
    if var is not None:
        # İkinci çağrı: yeni istek göndermiyoruz. Başarısız kalmışsa yeniden
        # denenebilmesi için ayrı bir anahtarla çağrılması gerekir.
        return var

    saglayici = saglayici_sec(siparis.magaza)
    islem = OdemeIslemi.objects.create(
        siparis=siparis, tur=OdemeIslemi.Tur.PROVIZYON, tutar=tutar,
        saglayici=saglayici.ad, istek_anahtari=anahtar, kullanici=kullanici,
        aciklama=f"Sipariş onayı · {para_yaz(tutar)} bloke")

    sonuc = saglayici.provizyon_al(siparis, tutar, anahtar)
    islem.sonucu_yaz(basarili=sonuc.basarili, saglayici_islem_no=sonuc.islem_no,
                     yanit=sonuc.yanit, hata_kodu=sonuc.hata_kodu,
                     hata_mesaji=sonuc.hata_mesaji)

    siparis.odeme_durumu = (Siparis.OdemeDurumu.PROVIZYON if sonuc.basarili
                            else Siparis.OdemeDurumu.BASARISIZ)
    siparis.save(update_fields=["odeme_durumu", "guncellendi"])
    return islem


# ==========================================================================
# ÇEKİM
# ==========================================================================
@transaction.atomic
def cekim_yap(siparis, kullanici=None, tutar=None):
    """
    Bloke edilen tutardan kesin tutarı çeker.

    Tartımdan sonra, sipariş hazırlandığında çağrılır. Tutar verilmezse
    siparişin `toplam` alanı kullanılır — tartım sonrası kesinleşmiş tutar.

    **Çekilen tutar blokeyi aşamaz.** Tartı beklenenden çok fazla çıkarsa
    bankadan ek tutar çekilemez; o durumda müşteriye sorulması gerekir.
    Sessizce fazla çekmek yerine hata veriyoruz.
    """
    provizyon = _basarili_islem(siparis, OdemeIslemi.Tur.PROVIZYON)
    if provizyon is None:
        raise ValidationError("Bu siparişte başarılı bir provizyon yok; önce bloke alınmalı.")
    if _basarili_islem(siparis, OdemeIslemi.Tur.BLOKE_COZ):
        raise ValidationError("Bu siparişin blokesi çözülmüş; çekim yapılamaz.")

    tutar = Decimal(str(tutar)) if tutar is not None else siparis.toplam
    if tutar <= SIFIR:
        raise ValidationError("Çekilecek tutar sıfırdan büyük olmalı.")
    if tutar > provizyon.tutar:
        raise ValidationError(
            f"Çekilecek tutar ({para_yaz(tutar)}) bloke edilenden "
            f"({para_yaz(provizyon.tutar)}) fazla. Tartı tahmini çok aştı; "
            f"müşteriyle görüşülmeden çekim yapılamaz.")

    anahtar = _anahtar(siparis, OdemeIslemi.Tur.CEKIM)
    var = _var_olan(anahtar)
    if var is not None:
        return var

    saglayici = saglayici_sec(siparis.magaza)
    islem = OdemeIslemi.objects.create(
        siparis=siparis, tur=OdemeIslemi.Tur.CEKIM, tutar=tutar,
        kaynak_islem=provizyon, saglayici=saglayici.ad,
        istek_anahtari=anahtar, kullanici=kullanici,
        aciklama=f"Tartım sonrası kesin tutar · {para_yaz(tutar)}")

    sonuc = saglayici.cekim_yap(siparis, tutar, provizyon.saglayici_islem_no, anahtar)
    islem.sonucu_yaz(basarili=sonuc.basarili, saglayici_islem_no=sonuc.islem_no,
                     yanit=sonuc.yanit, hata_kodu=sonuc.hata_kodu,
                     hata_mesaji=sonuc.hata_mesaji)

    if sonuc.basarili:
        siparis.cekilen_tutar = tutar
        siparis.odeme_durumu = Siparis.OdemeDurumu.CEKILDI
        siparis.save(update_fields=["cekilen_tutar", "odeme_durumu", "guncellendi"])
    return islem


# ==========================================================================
# BLOKE ÇÖZME
# ==========================================================================
@transaction.atomic
def bloke_coz(siparis, kullanici=None, sebep=""):
    """
    Blokeyi serbest bırakır. Sipariş iptal edildiğinde çağrılır.

    Çekim yapılmışsa bloke zaten kapanmıştır; o durumda iade gerekir, bu değil.
    """
    provizyon = _basarili_islem(siparis, OdemeIslemi.Tur.PROVIZYON)
    if provizyon is None:
        return None          # bloke yoksa çözecek bir şey de yok
    if _basarili_islem(siparis, OdemeIslemi.Tur.CEKIM):
        raise ValidationError("Bu siparişten para çekilmiş; bloke çözme değil iade gerekir.")

    anahtar = _anahtar(siparis, OdemeIslemi.Tur.BLOKE_COZ)
    var = _var_olan(anahtar)
    if var is not None:
        return var

    saglayici = saglayici_sec(siparis.magaza)
    islem = OdemeIslemi.objects.create(
        siparis=siparis, tur=OdemeIslemi.Tur.BLOKE_COZ, tutar=provizyon.tutar,
        kaynak_islem=provizyon, saglayici=saglayici.ad,
        istek_anahtari=anahtar, kullanici=kullanici,
        aciklama=sebep or "Sipariş iptal edildi")

    sonuc = saglayici.bloke_coz(siparis, provizyon.saglayici_islem_no, anahtar)
    islem.sonucu_yaz(basarili=sonuc.basarili, saglayici_islem_no=sonuc.islem_no,
                     yanit=sonuc.yanit, hata_kodu=sonuc.hata_kodu,
                     hata_mesaji=sonuc.hata_mesaji)

    if sonuc.basarili:
        siparis.odeme_durumu = Siparis.OdemeDurumu.BEKLIYOR
        siparis.save(update_fields=["odeme_durumu", "guncellendi"])
    return islem


# ==========================================================================
# İADE
# ==========================================================================
@transaction.atomic
def iade_et(siparis, tutar, kullanici=None, sebep=""):
    """
    Çekilmiş paradan iade yapar. Kusurlu ürün kararından sonra çağrılır.

    Kısmi iade olabilir; birden çok kez çağrılabilir. Toplam iade, çekilen
    tutarı aşamaz — her çağrıda deftere bakılıp kalan hesaplanıyor.
    """
    cekim = _basarili_islem(siparis, OdemeIslemi.Tur.CEKIM)
    if cekim is None:
        raise ValidationError("Bu siparişten para çekilmemiş; iade edilecek tutar yok.")

    tutar = Decimal(str(tutar))
    if tutar <= SIFIR:
        raise ValidationError("İade tutarı sıfırdan büyük olmalı.")

    onceki = sum((i.tutar for i in siparis.odeme_islemleri.filter(
        tur=OdemeIslemi.Tur.IADE, durum=OdemeIslemi.Durum.BASARILI)), SIFIR)
    kalan = cekim.tutar - onceki
    if tutar > kalan:
        raise ValidationError(
            f"İade tutarı ({para_yaz(tutar)}) iade edilebilecek kalandan "
            f"({para_yaz(kalan)}) fazla.")

    sira = siparis.odeme_islemleri.filter(tur=OdemeIslemi.Tur.IADE).count() + 1
    anahtar = _anahtar(siparis, OdemeIslemi.Tur.IADE, sira)
    var = _var_olan(anahtar)
    if var is not None:
        return var

    saglayici = saglayici_sec(siparis.magaza)
    islem = OdemeIslemi.objects.create(
        siparis=siparis, tur=OdemeIslemi.Tur.IADE, tutar=tutar,
        kaynak_islem=cekim, saglayici=saglayici.ad,
        istek_anahtari=anahtar, kullanici=kullanici,
        aciklama=sebep or "İade")

    sonuc = saglayici.iade_et(siparis, tutar, cekim.saglayici_islem_no, anahtar)
    islem.sonucu_yaz(basarili=sonuc.basarili, saglayici_islem_no=sonuc.islem_no,
                     yanit=sonuc.yanit, hata_kodu=sonuc.hata_kodu,
                     hata_mesaji=sonuc.hata_mesaji)

    if sonuc.basarili:
        toplam_iade = onceki + tutar
        siparis.cekilen_tutar = cekim.tutar - toplam_iade
        siparis.odeme_durumu = (Siparis.OdemeDurumu.IADE
                                if toplam_iade >= cekim.tutar
                                else Siparis.OdemeDurumu.KISMI_IADE)
        siparis.save(update_fields=["cekilen_tutar", "odeme_durumu", "guncellendi"])
    return islem
