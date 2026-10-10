"""
Bostanhane — bildirim modelleri

Bu dosya `bildirim/models.py` olarak kaydedilir.

### Niye defter tutuyoruz

Müşteri "bana haber vermediniz" der. Cevabı kesin olmalı: ne zaman, hangi numaraya,
hangi metin gitti, sağlayıcı ne dedi. Ödeme defterinde olduğu gibi burada da
**gönderilen her istek bir satır** — başarısız olanlar dahil.

### SMS uzunluğu — görünmeyen maliyet

Bir SMS 160 karakter sanılır. Doğru değil: mesajda **tek bir Türkçe karakter**
(ş, ğ, ı, İ, ö, ü, ç) varsa operatör UCS-2'ye düşer ve sınır **70 karaktere** iner.
"Siparişiniz alındı" yazmak ile "Siparisiniz alindi" yazmak arasında iki kat maliyet
farkı olabiliyor.

Türkçe karakterden vazgeçmiyoruz — müşteriye "Siparisiniz alindi" yazmak ucuz durur.
Ama kaç parça gittiğini **ölçüyoruz ve panelde gösteriyoruz** ki fatura sürpriz olmasın
ve uzun metinler fark edilsin.
"""

from django.conf import settings
from django.db import models

from core.models import ZamanDamgali

# GSM-7 alfabesinde olmayan tek karakter bile mesajı UCS-2'ye düşürür.
# Türkçe'de sorun çıkaranlar: ı İ ş Ş ğ Ğ (ç Ç ö Ö ü Ü GSM-7'de var).
GSM7_DISI = set("ıİşŞğĞ")

TEK_PARCA_GSM7, COK_PARCA_GSM7 = 160, 153
TEK_PARCA_UCS2, COK_PARCA_UCS2 = 70, 67


def sms_parca_sayisi(metin):
    """
    Bu metin kaç SMS olarak gider? (parça sayısı, alfabe) döner.

    Operatör tek mesaja sığmayan metni böler ve **her parçayı ayrı ücretlendirir**.
    Bölünmüş mesajda başlık bilgisi yer kapladığı için parça başına sınır da düşer
    (160 → 153, 70 → 67).
    """
    metin = metin or ""
    ucs2 = any(harf in GSM7_DISI for harf in metin)
    tek, cok = (TEK_PARCA_UCS2, COK_PARCA_UCS2) if ucs2 else (TEK_PARCA_GSM7, COK_PARCA_GSM7)
    alfabe = "UCS-2 (Türkçe karakter var)" if ucs2 else "GSM-7"
    uzunluk = len(metin)
    if uzunluk == 0:
        return 0, alfabe
    if uzunluk <= tek:
        return 1, alfabe
    return -(-uzunluk // cok), alfabe       # yukarı yuvarlama


class Bildirim(ZamanDamgali):
    """Müşteriye gönderilen tek bir mesaj."""

    class Kanal(models.TextChoices):
        SMS = "sms", "SMS"
        EPOSTA = "eposta", "E-posta"

    class Tur(models.TextChoices):
        SIPARIS_ALINDI = "siparis_alindi", "Sipariş alındı"
        KESIM_YAKLASTI = "kesim_yaklasti", "Kesim saati yaklaştı"
        GUN_KESILDI = "gun_kesildi", "Sipariş kesinleşti"
        URUN_BULUNAMADI = "urun_bulunamadi", "Ürün bulunamadı"
        YOLA_CIKTI = "yola_cikti", "Kurye yola çıktı"
        TESLIM_EDILDI = "teslim_edildi", "Teslim edildi"
        SIPARIS_IPTAL = "siparis_iptal", "Sipariş iptal edildi"
        TALEP_KARARI = "talep_karari", "Bildiriminize karar verildi"

    class Durum(models.TextChoices):
        BEKLIYOR = "bekliyor", "Bekliyor"
        GONDERILDI = "gonderildi", "Gönderildi"
        BASARISIZ = "basarisiz", "Başarısız"
        ATLANDI = "atlandi", "Atlandı"

    alici = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                              null=True, blank=True, related_name="bildirimler",
                              verbose_name="alıcı")
    siparis = models.ForeignKey("siparis.Siparis", on_delete=models.SET_NULL,
                                null=True, blank=True, related_name="bildirimler",
                                verbose_name="sipariş")
    kanal = models.CharField("kanal", max_length=10, choices=Kanal.choices)
    tur = models.CharField("tür", max_length=20, choices=Tur.choices)

    # Gönderim anındaki adres — kişi numarasını sonra değiştirse bile
    # "biz şu numaraya yazmıştık" belli olsun.
    adres = models.CharField("gönderilen adres", max_length=120,
                             help_text="Telefon numarası ya da e-posta adresi.")
    konu = models.CharField("konu", max_length=200, blank=True,
                            help_text="Yalnızca e-postada kullanılır.")
    metin = models.TextField("metin", max_length=2000)

    durum = models.CharField("durum", max_length=12, choices=Durum.choices,
                             default=Durum.BEKLIYOR)
    saglayici = models.CharField("sağlayıcı", max_length=30, blank=True)
    saglayici_mesaj_no = models.CharField("sağlayıcı mesaj no", max_length=100, blank=True)
    hata_mesaji = models.CharField("hata", max_length=300, blank=True)

    # Aynı bildirimin iki kez gitmesini engeller. Zamanlanmış görev iki kez
    # tetiklenirse ya da bir işlem tekrar edilirse müşteri aynı mesajı iki kez almaz.
    istek_anahtari = models.CharField("istek anahtarı", max_length=100, unique=True)
    gonderim_zamani = models.DateTimeField("gönderim zamanı", null=True, blank=True)

    class Meta:
        verbose_name = "bildirim"
        verbose_name_plural = "bildirimler"
        ordering = ["-olusturuldu"]
        indexes = [models.Index(fields=["siparis", "tur"]),
                   models.Index(fields=["durum", "olusturuldu"])]

    def __str__(self):
        return f"{self.get_tur_display()} · {self.adres}"

    @property
    def gonderildi_mi(self):
        return self.durum == self.Durum.GONDERILDI

    @property
    def parca_sayisi(self):
        """SMS kaç parça gitti. E-postada anlamsız, None döner."""
        if self.kanal != self.Kanal.SMS:
            return None
        return sms_parca_sayisi(self.metin)[0]

    @property
    def alfabe(self):
        if self.kanal != self.Kanal.SMS:
            return ""
        return sms_parca_sayisi(self.metin)[1]
