"""
Bostanhane — bildirim gönderimi

Bu dosya `bildirim/islemler.py` olarak kaydedilir.

Dışarıdan çağrılacak işlevler burada. Görünümler ve komutlar sağlayıcıyı doğrudan
çağırmaz; deftere yazma, çift gönderim koruması ve **hata yutma** burada.

### En önemli kural: bildirim siparişi bozamaz

`gonder()` **hiçbir koşulda istisna fırlatmıyor.** SMS firması çökmüş olabilir,
numara bozuk olabilir, ağ kopmuş olabilir — bunların hiçbiri müşterinin siparişini
engellememeli. Mesaj gitmezse deftere "başarısız" yazılır ve hayat devam eder.

Tersi olsaydı: SMS firması bir saat çökse, o saatte kimse sipariş veremezdi.
Bildirim siparişin yan etkisidir, şartı değil.

### Çift gönderim koruması

Her bildirimin bir istek anahtarı var: `<sipariş no>-<tür>`. Aynı anahtarla
ikinci çağrı yeni mesaj göndermez. Zamanlanmış görev iki kez tetiklenirse ya da
bir işlem tekrar edilirse müşteri aynı mesajı iki kez almaz.

### Deneme siparişleri

Vitrin test modundayken verilen siparişlerin bildirimleri **[DENEME] önekiyle**
gidiyor. Prova sırasında gerçek mesajla deneme mesajı karışmasın.

Önek 9 karakter yer kaplıyor ve bazı mesajları iki SMS parçasına çıkarıyor. Sorun
değil: deneme mesajları yalnızca provayı yapan kişiye gidiyor, müşteriye değil.
Gerçek satışta vitrin `acik` olacağı için önek hiç eklenmeyecek.
"""

import logging

from django.utils import timezone

from .metinler import (gun_kesildi, kesim_yaklasti, siparis_alindi, siparis_iptal,
                       talep_karari, teslim_edildi, urun_bulunamadi, yola_cikti)
from .models import Bildirim
from .saglayicilar import eposta_saglayici_sec, sms_saglayici_sec

kayit = logging.getLogger(__name__)

# tür → metin üreten işlev
METIN_URETICILERI = {
    Bildirim.Tur.SIPARIS_ALINDI: siparis_alindi,
    Bildirim.Tur.KESIM_YAKLASTI: kesim_yaklasti,
    Bildirim.Tur.GUN_KESILDI: gun_kesildi,
    Bildirim.Tur.URUN_BULUNAMADI: urun_bulunamadi,
    Bildirim.Tur.YOLA_CIKTI: yola_cikti,
    Bildirim.Tur.TESLIM_EDILDI: teslim_edildi,
    Bildirim.Tur.SIPARIS_IPTAL: siparis_iptal,
    Bildirim.Tur.TALEP_KARARI: talep_karari,
}


def _anahtar(siparis, tur, ek=""):
    temel = f"{siparis.numara}-{tur}"
    return f"{temel}-{ek}" if ek else temel


def _sms_gonder(bildirim, magaza):
    saglayici = sms_saglayici_sec(magaza)
    bildirim.saglayici = saglayici.ad
    return saglayici.gonder(bildirim.adres, bildirim.metin, bildirim.istek_anahtari)


def _eposta_gonder(bildirim):
    saglayici = eposta_saglayici_sec()
    bildirim.saglayici = saglayici.ad
    return saglayici.gonder(bildirim.adres, bildirim.konu, bildirim.metin,
                            bildirim.istek_anahtari)


def gonder(siparis, tur, *args, anahtar_eki="", **kwargs):
    """
    Siparişle ilgili bir bildirimi gönderir. **Asla istisna fırlatmaz.**

    SMS her zaman denenir (telefon zorunlu alan). E-posta yalnızca üyenin
    e-postası varsa — e-posta isteğe bağlı, çoğu üyede yok.

    Dönen: gönderilen `Bildirim` kayıtlarının listesi (boş olabilir).
    """
    try:
        return _gonder(siparis, tur, *args, anahtar_eki=anahtar_eki, **kwargs)
    except Exception:
        # Buraya düşmek bir hata demektir ama siparişi bozmasına izin vermiyoruz.
        kayit.exception("Bildirim gönderilemedi: %s %s", siparis.numara, tur)
        return []


def _gonder(siparis, tur, *args, anahtar_eki="", **kwargs):
    uretici = METIN_URETICILERI[tur]
    konu, sms_metni, eposta_metni = uretici(siparis, *args, **kwargs)

    if siparis.test_siparisi:
        sms_metni = f"[DENEME] {sms_metni}"
        konu = f"[DENEME] {konu}"

    uye = siparis.uye
    magaza = siparis.magaza
    cikti = []

    # -- SMS ---------------------------------------------------------------
    telefon = siparis.teslim_telefon or (uye.telefon if uye else "")
    anahtar = _anahtar(siparis, tur, anahtar_eki)
    if telefon and not Bildirim.objects.filter(istek_anahtari=anahtar).exists():
        bildirim = Bildirim.objects.create(
            alici=uye, siparis=siparis, kanal=Bildirim.Kanal.SMS, tur=tur,
            adres=telefon, metin=sms_metni, istek_anahtari=anahtar)
        sonuc = _sms_gonder(bildirim, magaza)
        _sonucu_yaz(bildirim, sonuc)
        cikti.append(bildirim)

    # -- E-posta -----------------------------------------------------------
    eposta = getattr(uye, "eposta", "") if uye else ""
    eposta_anahtar = f"{anahtar}-eposta"
    if eposta and not Bildirim.objects.filter(istek_anahtari=eposta_anahtar).exists():
        bildirim = Bildirim.objects.create(
            alici=uye, siparis=siparis, kanal=Bildirim.Kanal.EPOSTA, tur=tur,
            adres=eposta, konu=konu, metin=eposta_metni,
            istek_anahtari=eposta_anahtar)
        sonuc = _eposta_gonder(bildirim)
        _sonucu_yaz(bildirim, sonuc)
        cikti.append(bildirim)

    return cikti


def _sonucu_yaz(bildirim, sonuc):
    bildirim.durum = (Bildirim.Durum.GONDERILDI if sonuc.basarili
                      else Bildirim.Durum.BASARISIZ)
    bildirim.saglayici_mesaj_no = sonuc.mesaj_no
    bildirim.hata_mesaji = sonuc.hata_mesaji[:300]
    if sonuc.basarili:
        bildirim.gonderim_zamani = timezone.now()
    bildirim.save(update_fields=["durum", "saglayici", "saglayici_mesaj_no",
                                 "hata_mesaji", "gonderim_zamani", "guncellendi"])


# ==========================================================================
# Akıştan çağrılacak kısayollar
# ==========================================================================
def siparis_alindi_bildir(siparis):
    return gonder(siparis, Bildirim.Tur.SIPARIS_ALINDI)


def kesim_yaklasti_bildir(siparis, kalan_dakika):
    return gonder(siparis, Bildirim.Tur.KESIM_YAKLASTI, kalan_dakika)


def gun_kesildi_bildir(siparis):
    return gonder(siparis, Bildirim.Tur.GUN_KESILDI)


def urun_bulunamadi_bildir(siparis):
    """
    Bulunamayan ürünler için **tek** mesaj gönderir.

    Kalem kalem göndermiyoruz: üç ürün bulunamadıysa müşteriye üç SMS gitmesi
    hem pahalı hem rahatsız edici. Hepsi tek mesajda toplanıyor.
    """
    kalemler = [k for k in siparis.kalemler.all() if k.bulunamadi_mi]
    if not kalemler:
        return []
    return gonder(siparis, Bildirim.Tur.URUN_BULUNAMADI, kalemler)


def yola_cikti_bildir(siparis):
    return gonder(siparis, Bildirim.Tur.YOLA_CIKTI)


def teslim_edildi_bildir(siparis):
    return gonder(siparis, Bildirim.Tur.TESLIM_EDILDI)


def siparis_iptal_bildir(siparis):
    return gonder(siparis, Bildirim.Tur.SIPARIS_IPTAL)


def talep_karari_bildir(talep):
    # Anahtara talep numarası ekleniyor: aynı siparişte birden çok talep olabilir.
    return gonder(talep.siparis, Bildirim.Tur.TALEP_KARARI, talep,
                  anahtar_eki=str(talep.pk))
