"""
Bostanhane — bildirim sağlayıcıları

Bu dosya `bildirim/saglayicilar.py` olarak kaydedilir.

### Niye araya katman koyuyoruz

SMS firması seçilmedi. Seçildiğinde de değişebilir — fiyat, teslim oranı ya da
başlık sorunu yüzünden. Firmayı doğrudan çağırsaydık, değiştirmek bütün sipariş
akışını elden geçirmek olurdu.

Yeni firma geldiğinde `SmsSaglayici`'dan türeyen tek bir sınıf yazılıyor,
`SAGLAYICILAR` sözlüğüne bir satır ekleniyor, `.env`'de bir ayar değişiyor.
Başka hiçbir yer değişmiyor. (Ödemede aynısını yaptık, işe yaradı.)

### `DenemeSmsSaglayici` bugünden çalışıyor

Mesajı hiçbir yere göndermiyor, "gönderildi" diyor. Böylece bütün bildirim akışı
— sipariş alındı, kesim yaklaştı, yola çıktı — firma sözleşmesi olmadan baştan
sona denenebiliyor. Metinler panelde görünüyor, kaç SMS parçası ettiği ölçülüyor.

**Canlıda gerçek satış açılırken deneme göndericisi kullanılamaz:** `saglayici_sec`
bunu denetliyor. Müşteriye hiç mesaj gitmediği hâlde sistemde "gönderildi" yazması,
sessiz ve fark edilmesi zor bir hatadır.
"""

import uuid

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.mail import send_mail


class GonderimSonucu:
    """Sağlayıcıdan dönen cevabın tek biçimli hâli."""

    def __init__(self, basarili, mesaj_no="", hata_mesaji=""):
        self.basarili = basarili
        self.mesaj_no = mesaj_no
        self.hata_mesaji = hata_mesaji

    def __repr__(self):
        return f"<GonderimSonucu {'başarılı' if self.basarili else 'başarısız'} {self.mesaj_no}>"


class SmsSaglayici:
    """
    Bütün SMS firmalarının uyması gereken sözleşme.

    Dönüş `GonderimSonucu`; istisna fırlatılmıyor. Mesajın gitmemesi bir çökme
    değil, kaydedilecek bir sonuçtur — sipariş akışı bu yüzden durmamalı.

    ### Başlık (gönderen adı) niye sağlayıcının işi

    SMS sözleşmesi **asarge** adına; aynı hesabın altında iki başlık duracak:
    `BOSTANHANE` ve `SECMENNEDIYOR`. Hesapta birden fazla başlık olduğu için
    firmaya giden her istekte hangisiyle gönderileceği **açıkça** yazılmalı —
    yazılmazsa firma kendi varsayılanını kullanır ve Bostanhane siparişinin
    bildirimi öteki markanın adıyla gidebilir. Müşteri tanımadığı bir isimden
    mesaj alır, hatta dolandırıcılık sanır.

    Başlık mesaj metnine dahil değil; 70 karakter sınırını yemiyor.
    """

    ad = "tanimsiz"
    gercek_gonderim = True

    def __init__(self):
        self.baslik = str(getattr(settings, "SMS_BASLIK", "") or "").strip()

    def gonder(self, telefon, metin, istek_anahtari):
        raise NotImplementedError


class DenemeSmsSaglayici(SmsSaglayici):
    """Hiçbir yere göndermez, başarılı döner. Test modu içindir."""

    ad = "deneme"
    gercek_gonderim = False

    def gonder(self, telefon, metin, istek_anahtari):
        if not telefon:
            return GonderimSonucu(False, hata_mesaji="Telefon numarası boş.")
        zorlanan = _zorlanan_hata()
        if zorlanan is not None:
            return zorlanan
        return GonderimSonucu(True, mesaj_no=f"DENEME-SMS-{uuid.uuid4().hex[:12]}")


def _zorlanan_hata():
    """
    `DENEME_BILDIRIM_HATASI` ayarı doluysa bütün gönderimler başarısız döner.

    Hata yolunu denemek için: mesaj gitmeyince sipariş akışı duruyor mu, defterde
    iz kalıyor mu, müşteri ekranı bozuluyor mu. Bunu denemek için kodu geçici
    değiştirmek gerekmemeli — unutulup öyle kalabilir. Canlıda boş kalacak.
    """
    ayar = str(getattr(settings, "DENEME_BILDIRIM_HATASI", "") or "").strip()
    if not ayar:
        return None
    return GonderimSonucu(False, hata_mesaji=ayar)


class EpostaSaglayici:
    """
    E-posta — Django'nun kendi gönderimi.

    Ayar yapılmamışsa Django konsola yazar; bu da bir tür "deneme" modudur.
    E-posta SMS'in yerine geçmiyor: üyelerin e-posta vermesi isteğe bağlı, yani
    kapsama düşük. Yedek ve uzun metin (sipariş özeti) için duruyor.
    """

    ad = "django"

    def gonder(self, eposta, konu, metin, istek_anahtari):
        if not eposta:
            return GonderimSonucu(False, hata_mesaji="E-posta adresi boş.")
        zorlanan = _zorlanan_hata()
        if zorlanan is not None:
            return zorlanan
        try:
            gonderilen = send_mail(
                subject=konu,
                message=metin,
                from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
                recipient_list=[eposta],
                fail_silently=False,
            )
        except Exception as hata:                      # ağ, kimlik, biçim…
            return GonderimSonucu(False, hata_mesaji=str(hata)[:300])
        if not gonderilen:
            return GonderimSonucu(False, hata_mesaji="E-posta gönderilemedi.")
        return GonderimSonucu(True, mesaj_no=f"EPOSTA-{uuid.uuid4().hex[:12]}")


# SMS firması eklendikçe buraya satır eklenir.
SAGLAYICILAR = {
    DenemeSmsSaglayici.ad: DenemeSmsSaglayici,
}


def sms_saglayici_sec(magaza=None):
    """
    Hangi SMS firması kullanılacak? `.env`'deki `SMS_SAGLAYICI`, varsayılan "deneme".

    **Koruma:** vitrin gerçek satışa (`acik`) açıkken deneme göndericisi
    kullanılamaz. Sistemde "gönderildi" yazıp müşteriye hiçbir şey ulaşmaması,
    fark edilmesi en zor hatalardan biri — kimse şikâyet etmez, çünkü kimse
    bir şey beklemediğini bilmez.
    """
    ad = getattr(settings, "SMS_SAGLAYICI", DenemeSmsSaglayici.ad)
    sinif = SAGLAYICILAR.get(ad)
    if sinif is None:
        raise ImproperlyConfigured(
            f"Tanımsız SMS sağlayıcısı: {ad!r}. "
            f"Seçenekler: {', '.join(sorted(SAGLAYICILAR))}")

    saglayici = sinif()

    if magaza is not None:
        from core.models import SatisAyarlari
        if SatisAyarlari.getir(magaza).vitrin_acik_mi:
            if not sinif.gercek_gonderim:
                raise ImproperlyConfigured(
                    "Vitrin gerçek satışa açık ama SMS sağlayıcısı 'deneme'. "
                    "Müşteriye hiçbir bildirim gitmez, sistemde gönderilmiş görünür.")
            # Hesapta iki başlık var (BOSTANHANE / SECMENNEDIYOR). Hangisiyle
            # gönderileceğini yazmazsak firma kendi varsayılanını kullanır ve
            # Bostanhane müşterisine öteki markanın adıyla mesaj gider.
            if not saglayici.baslik:
                raise ImproperlyConfigured(
                    "Vitrin gerçek satışa açık ama SMS_BASLIK boş. Sözleşme asarge "
                    "adına ve hesapta birden fazla başlık var; başlık yazılmazsa "
                    "mesaj yanlış marka adıyla gidebilir. SMS_BASLIK=BOSTANHANE.")
    return saglayici


def eposta_saglayici_sec():
    return EpostaSaglayici()
