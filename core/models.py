"""
Bostanhane — core uygulaması modelleri

Bu dosya `core/models.py` yerine geçer.

Buradaki dört yapı sistemin iskeletidir:
  Magaza          → "Bostanhane Beyşehir"
  Mahalle         → mağazanın hizmet verdiği mahalle
  HaftalikTeslimGunu → mahallenin hangi günler ziyaret edildiği (kural)
  TeslimTakvimi   → belirli bir tarihteki somut teslimat (sipariş buna bağlanır)

Kural ile takvim neden ayrı? Kural "Müftü Mahallesi salı ve cuma" der.
Takvim ise "3 Ekim Cuma, kapasite 40, durum açık" der. Siparişler takvime bağlanır;
böylece bir günü kapatmak, kapasitesini değiştirmek veya tatil ilan etmek mümkün olur.
"""

from django.db import models
from django.utils import timezone
from datetime import datetime, timedelta, time


class ZamanDamgali(models.Model):
    """Bütün modellerin ortak alanları: ne zaman oluşturuldu, ne zaman güncellendi."""

    olusturuldu = models.DateTimeField("oluşturulma", auto_now_add=True)
    guncellendi = models.DateTimeField("güncellenme", auto_now=True)

    class Meta:
        abstract = True


class Gun(models.IntegerChoices):
    PAZARTESI = 0, "Pazartesi"
    SALI = 1, "Salı"
    CARSAMBA = 2, "Çarşamba"
    PERSEMBE = 3, "Perşembe"
    CUMA = 4, "Cuma"
    CUMARTESI = 5, "Cumartesi"
    PAZAR = 6, "Pazar"


class Magaza(ZamanDamgali):
    """Bir şube. Aynı zamanda ürünlerin tartılıp paketlendiği butik depodur."""

    ad = models.CharField("mağaza adı", max_length=120, help_text="Örnek: Bostanhane Beyşehir")
    slug = models.SlugField("kısa ad", max_length=140, unique=True,
                            help_text="Adreste görünecek hali. Örnek: beysehir")
    il = models.CharField("il", max_length=60)
    ilce = models.CharField("ilçe", max_length=60)
    adres = models.TextField("açık adres", blank=True)
    enlem = models.DecimalField("enlem", max_digits=9, decimal_places=6, null=True, blank=True)
    boylam = models.DecimalField("boylam", max_digits=9, decimal_places=6, null=True, blank=True)
    telefon = models.CharField("telefon", max_length=20, blank=True)
    eposta = models.EmailField("e-posta", blank=True)
    aktif = models.BooleanField("aktif", default=True,
                                help_text="Kapalıysa bu mağaza sipariş almaz.")

    class Meta:
        verbose_name = "mağaza"
        verbose_name_plural = "mağazalar"
        ordering = ["ad"]

    def __str__(self):
        return self.ad


class Mahalle(ZamanDamgali):
    """Mağazanın hizmet verdiği mahalle."""

    magaza = models.ForeignKey(Magaza, on_delete=models.CASCADE,
                               related_name="mahalleler", verbose_name="mağaza")
    ad = models.CharField("mahalle adı", max_length=120)
    slug = models.SlugField("kısa ad", max_length=140)
    gunluk_kapasite = models.PositiveIntegerField(
        "günlük teslimat kapasitesi", default=40,
        help_text="Bir teslim gününde kaç siparişe kadar alınabilir.")
    sira = models.PositiveIntegerField("sıra", default=0,
                                       help_text="Listelerde görünme sırası.")
    aktif = models.BooleanField("aktif", default=True)

    class Meta:
        verbose_name = "mahalle"
        verbose_name_plural = "mahalleler"
        ordering = ["sira", "ad"]
        unique_together = [("magaza", "slug")]

    def __str__(self):
        return f"{self.ad} — {self.magaza.ad}"

    def teslim_gunleri_metni(self):
        """'Salı ve Cuma' gibi okunur bir metin döner."""
        gunler = [k.get_gun_display() for k in self.haftalik_gunler.all()]
        if not gunler:
            return "Teslim günü tanımlı değil"
        if len(gunler) == 1:
            return gunler[0]
        return ", ".join(gunler[:-1]) + " ve " + gunler[-1]

    teslim_gunleri_metni.short_description = "teslim günleri"


class HaftalikTeslimGunu(ZamanDamgali):
    """Mahallenin haftalık teslim kuralı. Takvim bu kurala göre üretilir."""

    mahalle = models.ForeignKey(Mahalle, on_delete=models.CASCADE,
                                related_name="haftalik_gunler", verbose_name="mahalle")
    gun = models.IntegerField("teslim günü", choices=Gun.choices)
    teslim_baslangic = models.TimeField("teslimat başlangıç", default=time(9, 0))
    teslim_bitis = models.TimeField("teslimat bitiş", default=time(18, 0))
    kesim_gun_farki = models.PositiveSmallIntegerField(
        "kesim kaç gün önce", default=1,
        help_text="1 = teslimattan bir gün önce.")
    kesim_saati = models.TimeField("kesim saati", default=time(18, 0),
                                   help_text="Bu saatten sonra sipariş alınmaz.")
    kapasite = models.PositiveIntegerField(
        "kapasite", null=True, blank=True,
        help_text="Boş bırakılırsa mahallenin günlük kapasitesi kullanılır.")
    aktif = models.BooleanField("aktif", default=True)

    class Meta:
        verbose_name = "haftalık teslim günü"
        verbose_name_plural = "haftalık teslim günleri"
        ordering = ["mahalle", "gun"]
        unique_together = [("mahalle", "gun")]

    def __str__(self):
        return f"{self.mahalle.ad} — {self.get_gun_display()}"

    def gecerli_kapasite(self):
        return self.kapasite or self.mahalle.gunluk_kapasite


class TeslimTakvimi(ZamanDamgali):
    """Belirli bir tarihteki somut teslimat. Siparişler buna bağlanır."""

    class Durum(models.TextChoices):
        ACIK = "acik", "Açık"
        KESILDI = "kesildi", "Kesildi"
        TAMAMLANDI = "tamamlandi", "Tamamlandı"
        IPTAL = "iptal", "İptal"

    mahalle = models.ForeignKey(Mahalle, on_delete=models.CASCADE,
                                related_name="takvim", verbose_name="mahalle")
    tarih = models.DateField("teslim tarihi")
    kesim_zamani = models.DateTimeField("kesim zamanı")
    kapasite = models.PositiveIntegerField("kapasite", default=40)
    durum = models.CharField("durum", max_length=12, choices=Durum.choices, default=Durum.ACIK)
    aciklama = models.CharField("not", max_length=200, blank=True)

    class Meta:
        verbose_name = "teslim takvimi"
        verbose_name_plural = "teslim takvimi"
        ordering = ["tarih", "mahalle"]
        unique_together = [("mahalle", "tarih")]

    def __str__(self):
        return f"{self.mahalle.ad} — {self.tarih:%d.%m.%Y}"

    # -- yardımcılar ------------------------------------------------------
    @property
    def siparis_alinabilir(self):
        """Sipariş alınabilir mi? Durum açık ve kesim saati geçmemiş olmalı."""
        return self.durum == self.Durum.ACIK and timezone.localtime() < self.kesim_zamani

    @property
    def kesime_kalan(self):
        """Kesim saatine kalan süre. Geçtiyse None döner."""
        fark = self.kesim_zamani - timezone.localtime()
        return fark if fark.total_seconds() > 0 else None

    @classmethod
    def kural_uret(cls, kural: HaftalikTeslimGunu, hafta_sayisi: int = 8):
        """
        Bir haftalık kuraldan ileriye dönük takvim kayıtları üretir.
        Var olan kayıtlara dokunmaz; sadece eksik olanları ekler.
        """
        uretilen = []
        bugun = timezone.localdate()
        for hafta in range(hafta_sayisi):
            # kuralın gününe denk gelen ilk tarihi bul
            fark = (kural.gun - bugun.weekday()) % 7 + hafta * 7
            tarih = bugun + timedelta(days=fark)
            kesim_tarihi = tarih - timedelta(days=kural.kesim_gun_farki)
            kesim_zamani = timezone.make_aware(
                datetime.combine(kesim_tarihi, kural.kesim_saati)
            )
            if kesim_zamani <= timezone.localtime():
                continue  # kesim saati geçmiş, bu tarihi üretme
            kayit, yeni = cls.objects.get_or_create(
                mahalle=kural.mahalle,
                tarih=tarih,
                defaults={
                    "kesim_zamani": kesim_zamani,
                    "kapasite": kural.gecerli_kapasite(),
                },
            )
            if yeni:
                uretilen.append(kayit)
        return uretilen


class IlgiKaydi(ZamanDamgali):
    """
    Site yayına hazırlanırken bırakılan ilgi kayıtları.
    Açılışta ilk haber verilecek kitle burada birikir.
    """

    eposta = models.EmailField("e-posta")
    telefon = models.CharField("telefon", max_length=20, blank=True)
    mahalle_adi = models.CharField("mahalle", max_length=120, blank=True,
                                   help_text="Ziyaretçinin yazdığı mahalle adı.")
    kaynak = models.CharField("kaynak", max_length=60, blank=True,
                              help_text="Örnek: instagram, tanıdık, arama")
    haber_verildi = models.BooleanField("haber verildi", default=False)

    class Meta:
        verbose_name = "ilgi kaydı"
        verbose_name_plural = "ilgi kayıtları"
        ordering = ["-olusturuldu"]

    def __str__(self):
        return self.eposta
