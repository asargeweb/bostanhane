"""
Bostanhane — ödeme sağlayıcıları

Bu dosya `odeme/saglayicilar.py` olarak kaydedilir.

### Niye araya bir katman koyuyoruz

Sanal POS sağlayıcısı seçilmedi (iyzico / PayTR). Seçildiğinde de bir gün
değişebilir — komisyon oranı, provizyon süresi ya da hizmet kalitesi yüzünden.
Sağlayıcıyı doğrudan çağırsaydık, değiştirmek bütün sipariş akışını elden
geçirmek demek olurdu.

Burada dört işlemi tanımlıyoruz. Yeni sağlayıcı geldiğinde `Saglayici`'den
türeyen tek bir sınıf yazılıyor, başka hiçbir yer değişmiyor:

| İşlem | Ne yapar |
|---|---|
| `provizyon_al`  | Karttan tutarı bloke eder, para çekmez |
| `cekim_yap`     | Bloke edilen tutardan kesin tutarı çeker |
| `bloke_coz`     | Blokeyi serbest bırakır (sipariş iptal) |
| `iade_et`       | Çekilmiş paradan iade yapar |

### Niye `DenemeSaglayici` var

Vitrin bugün test modunda; gerçek para hareketi yok ama akışın denenmesi lazım.
Deneme sağlayıcısı her isteği başarılı sayıyor ve sahte bir işlem numarası
döndürüyor. Böylece "bloke et → tart → kesin tutarı çek" zinciri sağlayıcı
sözleşmesi olmadan baştan sona prova edilebiliyor.

**Canlıda gerçek satış açılırken deneme sağlayıcısı kullanılamaz** — `SAGLAYICI_SEC`
bunu denetliyor: vitrin `acik` moddayken deneme sağlayıcı istenirse hata veriyor.
"""

import uuid
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


class OdemeSonucu:
    """Sağlayıcıdan dönen cevabın tek biçimli hâli."""

    def __init__(self, basarili, islem_no="", yanit=None, hata_kodu="", hata_mesaji=""):
        self.basarili = basarili
        self.islem_no = islem_no
        self.yanit = yanit or {}
        self.hata_kodu = hata_kodu
        self.hata_mesaji = hata_mesaji

    def __repr__(self):
        return f"<OdemeSonucu {'başarılı' if self.basarili else 'başarısız'} {self.islem_no}>"


class Saglayici:
    """
    Bütün sağlayıcıların uyması gereken sözleşme.

    Dört işlemin de dönüşü `OdemeSonucu`. İstisna fırlatmıyoruz: ödeme
    reddi hata değil, olağan bir sonuç — "kart limiti yetmedi" bir çökme değil,
    müşteriye söylenecek bir cevaptır.
    """

    ad = "tanimsiz"
    gercek_para = True

    def provizyon_al(self, siparis, tutar, istek_anahtari):
        raise NotImplementedError

    def cekim_yap(self, siparis, tutar, provizyon_islem_no, istek_anahtari):
        raise NotImplementedError

    def bloke_coz(self, siparis, provizyon_islem_no, istek_anahtari):
        raise NotImplementedError

    def iade_et(self, siparis, tutar, cekim_islem_no, istek_anahtari):
        raise NotImplementedError


class DenemeSaglayici(Saglayici):
    """
    Gerçek para hareketi olmayan sağlayıcı. Test modu içindir.

    Her istek başarılı döner.

    **Hata yolunu denemek için:** `DENEME_ODEME_HATASI` ayarı doluysa bütün
    istekler o hatayla başarısız döner. `.env`'e bir satır:

        DENEME_ODEME_HATASI=51|Yetersiz bakiye

    Niye ayar: ödeme reddedildiğinde ne olduğu (sipariş açılmıyor mu, stok geri
    dönüyor mu, sepet duruyor mu) en az başarılı yol kadar önemli. Bunu denemek
    için kodu geçici değiştirmek gerekmemeli — unutulup öyle kalabilir.
    Boş bırakılırsa hiçbir etkisi yok; canlıda zaten boş.
    """

    ad = "deneme"
    gercek_para = False

    def _zorlanan_hata(self):
        ayar = str(getattr(settings, "DENEME_ODEME_HATASI", "") or "").strip()
        if not ayar:
            return None
        kod, _, mesaj = ayar.partition("|")
        return OdemeSonucu(False, hata_kodu=kod.strip() or "deneme_hata",
                           hata_mesaji=mesaj.strip() or "Deneme hatası.")

    def _sonuc(self, tutar, etiket):
        zorlanan = self._zorlanan_hata()
        if zorlanan is not None:
            return zorlanan
        if Decimal(str(tutar)) < 0:
            return OdemeSonucu(False, hata_kodu="negatif_tutar",
                               hata_mesaji="Tutar negatif olamaz.")
        return OdemeSonucu(True, islem_no=f"DENEME-{etiket}-{uuid.uuid4().hex[:12]}",
                           yanit={"deneme": True, "etiket": etiket, "tutar": str(tutar)})

    def provizyon_al(self, siparis, tutar, istek_anahtari):
        return self._sonuc(tutar, "PRV")

    def cekim_yap(self, siparis, tutar, provizyon_islem_no, istek_anahtari):
        return self._sonuc(tutar, "CEK")

    def bloke_coz(self, siparis, provizyon_islem_no, istek_anahtari):
        return self._sonuc(0, "COZ")

    def iade_et(self, siparis, tutar, cekim_islem_no, istek_anahtari):
        return self._sonuc(tutar, "IAD")


# Sağlayıcı eklendikçe buraya satır eklenir.
SAGLAYICILAR = {
    DenemeSaglayici.ad: DenemeSaglayici,
}


def saglayici_sec(magaza=None):
    """
    Bu mağazada hangi sağlayıcı kullanılacak?

    Şimdilik ayardan okunuyor (`ODEME_SAGLAYICI`, varsayılan "deneme").
    İleride mağaza başına farklı sağlayıcı gerekirse `SatisAyarlari`'na alan
    eklenir ve yalnızca bu işlev değişir.

    **Koruma:** Vitrin gerçek satışa (`acik`) açıkken deneme sağlayıcı
    kullanılamaz. Müşteri "ödedim" sanıp hiç para çekilmemesi, olabilecek en
    kötü hatalardan biri; kod seviyesinde engelliyoruz.
    """
    ad = getattr(settings, "ODEME_SAGLAYICI", DenemeSaglayici.ad)
    sinif = SAGLAYICILAR.get(ad)
    if sinif is None:
        raise ImproperlyConfigured(
            f"Tanımsız ödeme sağlayıcısı: {ad!r}. "
            f"Seçenekler: {', '.join(sorted(SAGLAYICILAR))}")

    if magaza is not None and not sinif.gercek_para:
        from core.models import SatisAyarlari
        if SatisAyarlari.getir(magaza).vitrin_acik_mi:
            raise ImproperlyConfigured(
                "Vitrin gerçek satışa açık ama ödeme sağlayıcısı 'deneme'. "
                "Gerçek bir sanal POS tanımlanmadan satış açılamaz: "
                "müşteri ödediğini sanır, para çekilmez.")
    return sinif()
