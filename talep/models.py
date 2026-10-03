"""
Bostanhane — talep (kusurlu ürün bildirimi) modelleri

Bu dosya `talep/models.py` olarak kaydedilir.

### Niye ayrı bir model, iç nota yazmak yetmiyor mu

Claude Code teslim onayını yazarken "sorun bildirildi" durumunu siparişin iç
notuna sabit bir işaret koyarak işaretlemişti — model olmadığı için mecburdu ve
doğru bir geçici çözümdü. Ama iç not serbest metin: mağaza yöneticisi bir
cümle eklerken işareti silerse sipariş sessizce otomatik onaylanır ve müşterinin
şikâyeti kaybolur.

Bu model o geçici çözümün yerine geçiyor. Bir talep şunları ayrı ayrı tutuyor:
hangi sipariş, hangi ürün, müşteri ne diyor, fotoğraf var mı, mağaza ne karar
verdi, ne kadar iade edildi, iade hangi ödeme işlemine bağlı.

### Niye kalem bazında

"Siparişte sorun var" diye tek kayıt tutsaydık kısmi iade hesaplanamazdı.
Müşteri üç kalemden birinde sorun yaşıyor; iade o kalemin tutarı kadar olmalı.
Kalem boş bırakılabiliyor — teslimat hiç gelmediyse ya da sorun siparişin
tamamıyla ilgiliyse.

### Fotoğraflar ve nesne depolama

Fotoğraf bir anlaşmazlığın kanıtı; kaybolmamalı. Railway'in diski kalıcı
olmadığı için nesne depolama (R2) yapılandırılmadan fotoğraf **alınmıyor** —
`gorsel_yuklenebilir_mi()` bunu söylüyor, form ona bakıyor. Sessizce kaybolan
bir kanıt, hiç alınmamış kanıttan kötüdür.
"""

from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

from core.araclar import para_yaz
from core.models import ZamanDamgali
from siparis.models import Siparis, SiparisKalemi

SIFIR = Decimal("0.00")


def gorsel_yuklenebilir_mi():
    """
    Fotoğraf alınabilir mi? Nesne depolama yapılandırılmamışsa hayır.

    Yerel geliştirmede (DEBUG) diske yazmak sorun değil; canlıda Railway'in
    diski kalıcı olmadığı için dosya sonraki dağıtımda kaybolur.
    """
    if settings.DEBUG:
        return True
    arka_uc = settings.STORAGES.get("default", {}).get("BACKEND", "")
    return "S3Storage" in arka_uc


class Talep(ZamanDamgali):
    """Müşterinin bir siparişle ilgili bildirdiği sorun."""

    class Tur(models.TextChoices):
        KUSURLU = "kusurlu", "Ürün kusurlu / bozuk"
        EKSIK = "eksik", "Ürün eksik ya da hiç gelmedi"
        YANLIS = "yanlis", "Yanlış ürün geldi"
        DIGER = "diger", "Diğer"

    class Durum(models.TextChoices):
        ACIK = "acik", "Açık — mağaza bakacak"
        INCELENIYOR = "inceleniyor", "İnceleniyor"
        KABUL = "kabul", "Kabul edildi — iade yapıldı"
        KISMI = "kismi", "Kısmen kabul edildi"
        RED = "red", "Reddedildi"

    # Müşterinin bildirebileceği süre — mağaza ayarından okunuyor
    # (`SatisAyarlari.talep_acma_suresi_saat`).

    siparis = models.ForeignKey(Siparis, on_delete=models.PROTECT,
                               related_name="talepler", verbose_name="sipariş")
    kalem = models.ForeignKey(SiparisKalemi, on_delete=models.SET_NULL,
                              null=True, blank=True, related_name="talepler",
                              verbose_name="ürün",
                              help_text="Boşsa sorun siparişin tamamıyla ilgili.")
    tur = models.CharField("sorun", max_length=10, choices=Tur.choices, default=Tur.KUSURLU)
    aciklama = models.TextField("müşterinin açıklaması", max_length=1000)

    durum = models.CharField("durum", max_length=12, choices=Durum.choices, default=Durum.ACIK)
    karar_notu = models.TextField("mağazanın kararı", max_length=1000, blank=True,
                                  help_text="Müşteriye gösterilir. Kararın sebebini yazın.")
    karar_veren = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                    null=True, blank=True, related_name="verdigi_kararlar",
                                    verbose_name="kararı veren")
    karar_zamani = models.DateTimeField("karar zamanı", null=True, blank=True)
    iade_tutari = models.DecimalField("iade edilen", max_digits=10, decimal_places=2,
                                      default=SIFIR,
                                      validators=[MinValueValidator(SIFIR)])
    # Bu talep için yapılan iade hangi ödeme işlemi.
    #
    # İki işe yarıyor: (1) "şu talebin parası şu işlemle gitti" diye izlenebilir
    # olması, (2) **çift iade koruması** — para gittikten sonra talebi kapatma
    # adımı bir sebeple başarısız olursa, yönetici tekrar denediğinde buraya
    # bakılıyor ve ikinci kez para gönderilmiyor.
    odeme_islemi = models.ForeignKey("odeme.OdemeIslemi", on_delete=models.SET_NULL,
                                     null=True, blank=True, related_name="talepler",
                                     verbose_name="iade işlemi")

    class Meta:
        verbose_name = "talep"
        verbose_name_plural = "talepler"
        ordering = ["-olusturuldu"]
        indexes = [models.Index(fields=["siparis", "durum"])]

    def __str__(self):
        hedef = self.kalem.urun_adi if self.kalem_id else "sipariş geneli"
        return f"{self.siparis.numara} · {hedef} · {self.get_tur_display()}"

    @property
    def acik_mi(self):
        """Mağaza henüz karar vermedi. Açık talebi olan sipariş otomatik onaylanmaz."""
        return self.durum in (self.Durum.ACIK, self.Durum.INCELENIYOR)

    @property
    def karara_baglandi_mi(self):
        return not self.acik_mi

    @property
    def en_fazla_iade(self):
        """
        Bu talep için iade edilebilecek üst sınır.

        Kalem belliyse o kalemin tutarı, değilse siparişin çekilen tutarı.
        Mağaza yöneticisinin yanlışlıkla fazla iade yazmasını engelliyor.
        """
        if self.kalem_id:
            return self.kalem.tutar
        return self.siparis.cekilen_tutar or self.siparis.toplam

    def clean(self):
        hatalar = {}
        if self.kalem_id and self.kalem.siparis_id != self.siparis_id:
            hatalar["kalem"] = "Seçilen ürün bu siparişe ait değil."
        if self.iade_tutari and self.iade_tutari > self.en_fazla_iade:
            hatalar["iade_tutari"] = (
                f"İade tutarı en fazla {para_yaz(self.en_fazla_iade)} olabilir.")
        if self.karara_baglandi_mi and not self.karar_notu.strip():
            hatalar["karar_notu"] = "Karar verirken müşteriye bir açıklama yazın."
        if hatalar:
            raise ValidationError(hatalar)

    @classmethod
    def acilabilir_mi(cls, siparis):
        """
        Bu siparişe şimdi talep açılabilir mi? (uygun_mu, sebep) döner.

        Süre `SatisAyarlari.talep_acma_suresi_saat`'ten okunuyor; panelden
        değişiyor, koda gömülü değil.
        """
        from core.models import SatisAyarlari

        if siparis.durum != Siparis.Durum.TESLIM_EDILDI:
            return False, "Bu sipariş henüz teslim edilmedi."
        if siparis.teslim_zamani is None:
            return False, "Teslim zamanı kayıtlı değil; mağazayla görüşün."
        saat = SatisAyarlari.getir(siparis.magaza).talep_acma_suresi_saat
        son = siparis.teslim_zamani + timezone.timedelta(hours=saat)
        if timezone.now() > son:
            return False, (f"Bildirim süresi doldu. Teslimattan sonra {saat} saat "
                           f"içinde bildirilmesi gerekiyor.")
        return True, ""


class TalepGorseli(ZamanDamgali):
    """Müşterinin yüklediği fotoğraf. Anlaşmazlıkta kanıt; silinmez."""

    talep = models.ForeignKey(Talep, on_delete=models.CASCADE,
                              related_name="gorseller", verbose_name="talep")
    gorsel = models.ImageField("fotoğraf", upload_to="talep/")
    sira = models.PositiveSmallIntegerField("sıra", default=0)

    class Meta:
        verbose_name = "talep fotoğrafı"
        verbose_name_plural = "talep fotoğrafları"
        ordering = ["sira", "pk"]

    def __str__(self):
        return f"{self.talep} · fotoğraf {self.sira + 1}"
