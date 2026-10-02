"""
Bostanhane — ödeme modelleri

Bu dosya `odeme/models.py` olarak kaydedilir.

### Neden ayrı bir defter

`Siparis` üzerinde zaten `provizyon_tutari`, `cekilen_tutar` ve `odeme_durumu` var.
Onlar siparişin **şu anki hâli**. Burada tutulan ise **ne olduğu**: ne zaman bloke
edildi, ne zaman çekildi, ne kadar iade edildi, sağlayıcı ne dedi.

Bu ayrım bir gün lazım olacak: müşteri "param çekilmemiş" der, banka "çekilmiş" der.
O tartışma sağlayıcı işlem numarasıyla çözülür, siparişteki tek bir sayıyla değil.
Para işlerinde tek sayı değil, defter tutulur — stok defterinde de aynısını yaptık.

### Kart bilgisi burada da yok

Hiçbir alanda kart numarası, son kullanma tarihi veya CVV **tutulmaz**. Sağlayıcının
döndürdüğü ham yanıt `yanit` alanına yazılırken kart alanları temizlenir
(`yaniti_temizle`). Bu bir tercih değil, PCI-DSS gereği.

### Sağlayıcı seçilmedi, model bekleyemez

iyzico mu PayTR mi belli değil. Ama provizyon akışı (bloke et → tart → kesin tutarı çek)
sağlayıcıdan bağımsız. Model şimdi yazılıyor, sağlayıcı gelince `odeme/saglayicilar/`
altına tek bir sınıf eklenecek; buradaki hiçbir şey değişmeyecek.

`DenemeSaglayici` bugünden çalışıyor: vitrin test modundayken gerçek para hareketi
olmadan bütün akış prova edilebiliyor.
"""

from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction

from core.araclar import para_yaz
from core.models import ZamanDamgali
from siparis.models import Siparis

SIFIR = Decimal("0.00")

# Sağlayıcı yanıtında asla saklanmayacak alan adları.
GIZLI_ALANLAR = {
    "cardnumber", "cardnum", "card_number", "pan", "cc", "ccno",
    "cvv", "cvc", "cvv2", "securitycode", "security_code",
    "expiry", "expirymonth", "expiryyear", "expire_month", "expire_year",
    "cardholdername", "card_holder_name", "password", "sifre",
}


def yaniti_temizle(veri):
    """
    Sağlayıcı yanıtından kart alanlarını söker.

    Sağlayıcılar bazen gönderdiğimiz isteği yanıtta aynen geri döndürür; kart
    numarası o yoldan loglara sızar. Kaydetmeden önce buradan geçiyoruz.
    İç içe sözlük ve listeleri de tarar.
    """
    if isinstance(veri, dict):
        temiz = {}
        for anahtar, deger in veri.items():
            if str(anahtar).lower().replace("-", "").replace("_", "") in GIZLI_ALANLAR:
                temiz[anahtar] = "***"
            else:
                temiz[anahtar] = yaniti_temizle(deger)
        return temiz
    if isinstance(veri, (list, tuple)):
        return [yaniti_temizle(x) for x in veri]
    return veri


class OdemeIslemi(ZamanDamgali):
    """Bir siparişte yapılan tek bir para hareketi."""

    class Tur(models.TextChoices):
        PROVIZYON = "provizyon", "Provizyon (bloke)"
        CEKIM = "cekim", "Çekim"
        IADE = "iade", "İade"
        BLOKE_COZ = "bloke_coz", "Bloke çözüldü"

    class Durum(models.TextChoices):
        BEKLIYOR = "bekliyor", "Bekliyor"
        BASARILI = "basarili", "Başarılı"
        BASARISIZ = "basarisiz", "Başarısız"

    siparis = models.ForeignKey(Siparis, on_delete=models.PROTECT,
                                related_name="odeme_islemleri", verbose_name="sipariş")
    tur = models.CharField("işlem", max_length=12, choices=Tur.choices)
    durum = models.CharField("durum", max_length=10, choices=Durum.choices,
                             default=Durum.BEKLIYOR)
    tutar = models.DecimalField("tutar", max_digits=10, decimal_places=2)

    # Çekim ve iade hangi provizyona dayanıyor. Zincir böyle takip ediliyor:
    # provizyon → çekim → iade.
    kaynak_islem = models.ForeignKey("self", on_delete=models.PROTECT, null=True, blank=True,
                                     related_name="bagli_islemler", verbose_name="kaynak işlem")

    saglayici = models.CharField("sağlayıcı", max_length=20)
    saglayici_islem_no = models.CharField("sağlayıcı işlem no", max_length=100, blank=True,
                                          help_text="Bankayla konuşurken bu numara kullanılır.")
    # Aynı isteğin iki kez gitmesini engeller. Ağ koptuğunda ya da kullanıcı
    # iki kez tıkladığında çift çekim olmasın diye: aynı anahtarla ikinci kayıt
    # açılamaz, var olan döner.
    istek_anahtari = models.CharField("istek anahtarı", max_length=80, unique=True)

    hata_kodu = models.CharField("hata kodu", max_length=40, blank=True)
    hata_mesaji = models.CharField("hata mesajı", max_length=300, blank=True)
    yanit = models.JSONField("sağlayıcı yanıtı", default=dict, blank=True,
                             help_text="Kart alanları temizlenmiş ham yanıt.")

    kullanici = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                  null=True, blank=True, related_name="odeme_islemleri",
                                  verbose_name="işlemi yapan",
                                  help_text="Kendiliğinden çalışan işlemlerde boştur.")
    aciklama = models.CharField("açıklama", max_length=200, blank=True)

    class Meta:
        verbose_name = "ödeme işlemi"
        verbose_name_plural = "ödeme işlemleri"
        ordering = ["-olusturuldu"]
        indexes = [models.Index(fields=["siparis", "tur", "durum"])]

    def __str__(self):
        return f"{self.siparis.numara} · {self.get_tur_display()} · {para_yaz(self.tutar)}"

    @property
    def basarili_mi(self):
        return self.durum == self.Durum.BASARILI

    def sonucu_yaz(self, *, basarili, saglayici_islem_no="", yanit=None,
                   hata_kodu="", hata_mesaji=""):
        """Sağlayıcıdan dönen sonucu işler. Yanıt kart alanlarından arındırılır."""
        self.durum = self.Durum.BASARILI if basarili else self.Durum.BASARISIZ
        self.saglayici_islem_no = saglayici_islem_no or self.saglayici_islem_no
        self.yanit = yaniti_temizle(yanit or {})
        self.hata_kodu = hata_kodu[:40]
        self.hata_mesaji = hata_mesaji[:300]
        self.save(update_fields=["durum", "saglayici_islem_no", "yanit",
                                 "hata_kodu", "hata_mesaji", "guncellendi"])
        return self


# ==========================================================================
# SİPARİŞ ÖZETİ — defterden hesaplanır
# ==========================================================================
def siparis_ozeti(siparis):
    """
    Siparişin para durumu, defterden hesaplanarak.

    `Siparis.cekilen_tutar` alanı tek bir sayı tutuyor; burada o sayının
    nereden geldiği görünüyor. İkisi tutmuyorsa bir yerde hata var demektir.
    """
    islemler = siparis.odeme_islemleri.filter(durum=OdemeIslemi.Durum.BASARILI)
    toplam = {tur: SIFIR for tur, _ in OdemeIslemi.Tur.choices}
    for islem in islemler:
        toplam[islem.tur] += islem.tutar
    cekilen = toplam[OdemeIslemi.Tur.CEKIM] - toplam[OdemeIslemi.Tur.IADE]
    return {
        "bloke": toplam[OdemeIslemi.Tur.PROVIZYON],
        "cekilen": cekilen,
        "iade": toplam[OdemeIslemi.Tur.IADE],
        "bloke_cozuldu": toplam[OdemeIslemi.Tur.BLOKE_COZ] > SIFIR,
        "acik_bloke": (toplam[OdemeIslemi.Tur.PROVIZYON]
                       if not toplam[OdemeIslemi.Tur.BLOKE_COZ] else SIFIR),
    }
