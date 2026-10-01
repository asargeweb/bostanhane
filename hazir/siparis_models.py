"""
Bostanhane — siparis uygulaması modelleri

Bu dosya `siparis/models.py` yerine geçer.

Dört model var:

  Sepet         → henüz siparişe dönmemiş seçimler. Üyenin ya da ziyaretçinin.
  SepetKalemi   → sepetteki bir satır. Fiyatı CANLI okur.
  Siparis       → verilmiş sipariş. Fiyatı, adresi, tutarı DONDURULMUŞ.
  SiparisKalemi → siparişteki bir satır. Ürün adı ve fiyatı kopyalanmıştır.

**Sepet ile sipariş arasındaki fark, bu dosyanın en önemli fikri.**

Sepet canlıdır: fiyat panelden değişirse sepetteki tutar da değişir, doğru olan budur —
müşteri ödeme anındaki fiyatı öder. Sipariş ise dondurulmuştur: ürünün adı, birimi,
birim fiyatı, teslimat adresi, hepsi sipariş anında **kopyalanır**. Ertesi gün fiyat
değişse ya da müşteri adresini silse bile geçmiş sipariş olduğu gibi kalır. Fatura,
iade ve raporlar bunu gerektirir.

**Tartı ve bulunamayan ürün aynı mekanizmadan geçer.** Her satırda iki miktar var:
`siparis_miktari` (müşterinin istediği) ve `teslim_miktari` (gerçekte giden).
Tartıda 940 g çıktıysa teslim miktarı 0,940; ürün hiç bulunamadıysa 0. Para
`teslim_miktari` üzerinden çekilir. Tek kavram, iki iş.
"""

from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils import timezone

from core.models import Magaza, SatisAyarlari, TeslimTakvimi, ZamanDamgali
from katalog.models import MagazaUrun, StokHareketi

SIFIR = Decimal("0.00")


def kurus(tutar):
    """Para tutarını iki haneye yuvarlar. Her yerde aynı yuvarlama kullanılsın diye."""
    return Decimal(str(tutar)).quantize(Decimal("0.01"))


class Kanal(models.TextChoices):
    YEREL = "yerel", "Yerel teslimat"
    KARGO = "kargo", "Kargo"
    KURUMSAL = "kurumsal", "Kurumsal"


# ==========================================================================
# SEPET
# ==========================================================================
class Sepet(ZamanDamgali):
    """
    Bir kişinin bir mağazadaki açık sepeti.

    Üye girişi yapılmadan da sepet kurulabilsin diye `uye` boş olabiliyor;
    o durumda oturum anahtarıyla tutuluyor. Üye giriş yapınca ziyaretçi sepeti
    üyeninkiyle birleştirilir (`birlestir`).
    """

    uye = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                            null=True, blank=True, related_name="sepetler",
                            verbose_name="üye")
    oturum_anahtari = models.CharField("oturum anahtarı", max_length=40, blank=True,
                                       help_text="Giriş yapmamış ziyaretçinin sepeti.")
    magaza = models.ForeignKey(Magaza, on_delete=models.CASCADE,
                               related_name="sepetler", verbose_name="mağaza")
    teslim_takvimi = models.ForeignKey(
        TeslimTakvimi, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="sepetler", verbose_name="teslim günü")
    adres = models.ForeignKey("hesaplar.Adres", on_delete=models.SET_NULL,
                              null=True, blank=True, related_name="sepetler",
                              verbose_name="teslimat adresi")

    class Meta:
        verbose_name = "sepet"
        verbose_name_plural = "sepetler"
        ordering = ["-guncellendi"]
        constraints = [
            models.UniqueConstraint(fields=["uye", "magaza"], name="uye_basina_tek_sepet",
                                    condition=models.Q(uye__isnull=False)),
            models.UniqueConstraint(fields=["oturum_anahtari", "magaza"],
                                    name="oturum_basina_tek_sepet",
                                    condition=models.Q(uye__isnull=True)),
        ]

    def __str__(self):
        sahip = self.uye.ad_soyad if self.uye else "ziyaretçi"
        return f"{sahip} sepeti — {self.kalem_sayisi} ürün"

    # -- yardımcılar -------------------------------------------------------
    @property
    def ayarlar(self):
        return SatisAyarlari.getir(self.magaza)

    @property
    def kalem_sayisi(self):
        return self.kalemler.count()

    @property
    def bos_mu(self):
        return not self.kalemler.exists()

    @property
    def ara_toplam(self):
        """Ürün tutarları toplamı. Tartılı üründe tahmini tutar."""
        return kurus(sum((k.tutar for k in self.kalemler.all()), SIFIR))

    @property
    def teslimat_ucreti(self):
        return self.ayarlar.teslimat_ucreti_hesapla(self.ara_toplam)

    @property
    def toplam(self):
        return kurus(self.ara_toplam + self.teslimat_ucreti)

    @property
    def provizyon_toplami(self):
        """
        Karttan bloke edilecek tutar.

        Tampon yalnızca **tartılı** kalemlere uygulanır: sabit fiyatlı üründe
        sürpriz yok, müşterinin parasını gereksiz bloke etmeyelim.
        """
        toplam = SIFIR
        for kalem in self.kalemler.select_related("magaza_urun__urun"):
            toplam += kalem.provizyon_tutari
        return kurus(toplam + self.teslimat_ucreti)

    @property
    def tartili_var_mi(self):
        return any(k.magaza_urun.urun.tartili_mi for k in self.kalemler.all())

    # -- sepet kuralları ---------------------------------------------------
    @property
    def eksik_tutar(self):
        """Minimum sepete ne kadar kaldı? Yeterliyse None."""
        return self.ayarlar.sepet_eksigi(self.ara_toplam)

    @property
    def ucretsize_kalan(self):
        return self.ayarlar.ucretsize_kalan(self.ara_toplam)

    def siparise_hazir_mi(self):
        """
        Sipariş verilebilir mi? (uygun_mu, sebep) döner.
        Sebep müşteriye gösterilecek metindir.
        """
        if self.bos_mu:
            return False, "Sepetiniz boş."
        eksik = self.eksik_tutar
        if eksik:
            return False, f"Minimum sepet tutarı {self.ayarlar.min_sepet_tutari:.0f} ₺. " \
                          f"{eksik:.2f} ₺ daha eklemelisiniz."
        if self.teslim_takvimi is None:
            return False, "Teslim günü seçilmedi."
        if not self.teslim_takvimi.siparis_alinabilir:
            return False, "Seçtiğiniz teslim günü için sipariş saati doldu. " \
                          "Lütfen başka bir gün seçin."
        if self.adres is None:
            return False, "Teslimat adresi seçilmedi."
        for kalem in self.kalemler.select_related("magaza_urun__urun"):
            uygun, sebep = kalem.uygun_mu()
            if not uygun:
                return False, sebep
        return True, ""

    # -- sepet işlemleri ---------------------------------------------------
    def ekle(self, magaza_urun, miktar):
        """
        Ürünü sepete ekler ya da miktarını artırır.
        Zaten varsa **üstüne ekler**, değiştirmez — kullanıcı iki kez bastıysa niyeti budur.
        """
        kalem = self.kalemler.filter(magaza_urun=magaza_urun).first()
        if kalem:
            kalem.miktar += Decimal(str(miktar))
        else:
            kalem = SepetKalemi(sepet=self, magaza_urun=magaza_urun,
                                miktar=Decimal(str(miktar)))
        kalem.full_clean()
        kalem.save()
        return kalem

    def birlestir(self, kaynak_sepet):
        """
        Ziyaretçi sepetini üye sepetine katar. Giriş yapınca çağrılır.
        Aynı ürün iki sepette varsa miktarlar toplanır.
        """
        if kaynak_sepet.pk == self.pk:
            return
        for kalem in kaynak_sepet.kalemler.all():
            self.ekle(kalem.magaza_urun, kalem.miktar)
        kaynak_sepet.delete()

    @transaction.atomic
    def siparise_cevir(self, kullanici=None, kanal=Kanal.YEREL):
        """
        Sepeti siparişe dönüştürür ve sepeti boşaltır.

        Burada olan dört şey:
          1. Satırlar **kopyalanır** (ad, birim, fiyat dondurulur)
          2. Teslimat adresi **kopyalanır** (müşteri sonra silse de sipariş bozulmaz)
          3. Stok düşülür — **şimdi**, kesim saatinde değil: aradaki saatlerde
             başka müşteri aynı son kavanozu almasın
          4. Tutarlar hesaplanıp dondurulur
        """
        uygun, sebep = self.siparise_hazir_mi()
        if not uygun:
            raise ValidationError(sebep)

        ayarlar = self.ayarlar
        siparis = Siparis.objects.create(
            uye=self.uye,
            magaza=self.magaza,
            teslim_takvimi=self.teslim_takvimi,
            kanal=kanal,
            test_siparisi=ayarlar.test_modunda_mi,
            **Siparis.adres_kopyasi(self.adres),
        )

        for kalem in self.kalemler.select_related("magaza_urun__urun",
                                                  "magaza_urun__urun__birim"):
            SiparisKalemi.objects.create(
                siparis=siparis,
                magaza_urun=kalem.magaza_urun,
                urun_adi=kalem.magaza_urun.urun.ad,
                birim_adi=kalem.magaza_urun.urun.birim.kisaltma,
                tartili_mi=kalem.magaza_urun.urun.tartili_mi,
                birim_fiyat=kalem.magaza_urun.fiyat,
                siparis_miktari=kalem.miktar,
            )
            # Stok takipli üründe rezerve et. Takipsizde hiçbir şey olmaz.
            kalem.magaza_urun.stok_dus(
                kalem.miktar, kullanici=kullanici,
                aciklama=f"Sipariş {siparis.numara}")

        siparis.tutarlari_hesapla(kaydet=True)
        self.kalemler.all().delete()
        self.teslim_takvimi = None
        self.save(update_fields=["teslim_takvimi", "guncellendi"])
        return siparis


class SepetKalemi(ZamanDamgali):
    """Sepetteki bir satır. Fiyatı canlı okur — ödeme anındaki fiyat geçerlidir."""

    sepet = models.ForeignKey(Sepet, on_delete=models.CASCADE,
                              related_name="kalemler", verbose_name="sepet")
    magaza_urun = models.ForeignKey(MagazaUrun, on_delete=models.CASCADE,
                                    related_name="sepet_kalemleri", verbose_name="ürün")
    miktar = models.DecimalField("miktar", max_digits=10, decimal_places=3)

    class Meta:
        verbose_name = "sepet kalemi"
        verbose_name_plural = "sepet kalemleri"
        ordering = ["magaza_urun__urun__kategori__sira", "magaza_urun__urun__ad"]
        unique_together = [("sepet", "magaza_urun")]

    def __str__(self):
        return f"{self.magaza_urun.urun.ad} × {self.miktar_metni}"

    @property
    def urun(self):
        return self.magaza_urun.urun

    @property
    def miktar_metni(self):
        """'1,5 kg' · '2 demet' — kilogramda bir altı gram gösterilir."""
        birim = self.urun.birim
        if birim.kilogram_mi and self.miktar < 1:
            return f"{int(self.miktar * 1000)} g"
        sayi = f"{self.miktar.normalize():f}".replace(".", ",")
        return f"{sayi} {birim.kisaltma}"

    @property
    def tutar(self):
        return self.magaza_urun.tutar(self.miktar) or SIFIR

    @property
    def provizyon_tutari(self):
        return self.magaza_urun.provizyon_tutari(self.miktar) or SIFIR

    def uygun_mu(self):
        """Bu satır hâlâ sipariş edilebilir mi? (uygun, sebep)"""
        if not self.magaza_urun.satista_mi:
            return False, f"{self.urun.ad} şu an satışta değil, sepetten çıkarın."
        if not self.magaza_urun.stok_yeterli_mi(self.miktar):
            kalan = self.magaza_urun.stok
            return False, f"{self.urun.ad} için yeterli stok yok (kalan: {kalan})."
        return True, ""

    def clean(self):
        super().clean()
        if self.miktar is None or self.miktar <= 0:
            raise ValidationError({"miktar": "Miktar sıfırdan büyük olmalı."})

        adim = self.urun.satis_adimi
        if adim and (self.miktar % adim) != 0:
            raise ValidationError({
                "miktar": f"{self.urun.ad} {self.urun.satis_adimi_metni} satılıyor; "
                          f"miktar bu adımın katı olmalı."
            })
        if not self.urun.birim.kesirli and self.miktar != self.miktar.to_integral_value():
            raise ValidationError({
                "miktar": f"{self.urun.birim.ad} kesirli satılmaz, tam sayı girin."
            })
        if not self.magaza_urun.stok_yeterli_mi(self.miktar):
            raise ValidationError({
                "miktar": f"Yeterli stok yok. Kalan: {self.magaza_urun.stok}."
            })


# ==========================================================================
# SİPARİŞ
# ==========================================================================
class Siparis(ZamanDamgali):
    """
    Verilmiş sipariş. Tutarı, adresi ve ürün bilgileri dondurulmuştur.

    `numara` müşteriye söylenen numaradır: BH-2026-001042.
    """

    class Durum(models.TextChoices):
        ALINDI = "alindi", "Alındı"
        KESILDI = "kesildi", "Kesildi"
        HAZIRLANIYOR = "hazirlaniyor", "Hazırlanıyor"
        YOLDA = "yolda", "Yolda"
        TESLIM_EDILDI = "teslim_edildi", "Teslim edildi"
        IPTAL = "iptal", "İptal"

    class OdemeDurumu(models.TextChoices):
        BEKLIYOR = "bekliyor", "Bekliyor"
        PROVIZYON = "provizyon", "Provizyon alındı"
        CEKILDI = "cekildi", "Çekildi"
        KISMI_IADE = "kismi_iade", "Kısmi iade"
        IADE = "iade", "İade edildi"
        BASARISIZ = "basarisiz", "Başarısız"

    numara = models.CharField("sipariş no", max_length=20, unique=True, editable=False)
    uye = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
                            related_name="siparisler", verbose_name="üye")
    magaza = models.ForeignKey(Magaza, on_delete=models.PROTECT,
                               related_name="siparisler", verbose_name="mağaza")
    teslim_takvimi = models.ForeignKey(
        TeslimTakvimi, on_delete=models.PROTECT, null=True, blank=True,
        related_name="siparisler", verbose_name="teslim günü",
        help_text="Kargo siparişinde boştur.")
    kanal = models.CharField("kanal", max_length=10, choices=Kanal.choices, default=Kanal.YEREL)

    # -- adres kopyası -----------------------------------------------------
    # Müşteri adresini silse ya da değiştirse bile sipariş olduğu gibi kalsın.
    teslim_ad_soyad = models.CharField("teslim alacak kişi", max_length=120)
    teslim_telefon = models.CharField("teslimat telefonu", max_length=10)
    teslim_acik_adres = models.TextField("açık adres")
    teslim_mahalle = models.CharField("mahalle", max_length=120)
    teslim_ilce = models.CharField("ilçe", max_length=60)
    teslim_il = models.CharField("il", max_length=40)
    teslim_tarif = models.CharField("kuryeye not", max_length=200, blank=True)
    teslim_enlem = models.DecimalField("enlem", max_digits=9, decimal_places=6,
                                       null=True, blank=True)
    teslim_boylam = models.DecimalField("boylam", max_digits=9, decimal_places=6,
                                        null=True, blank=True)

    # -- tutarlar (dondurulmuş) -------------------------------------------
    ara_toplam = models.DecimalField("ara toplam", max_digits=10, decimal_places=2, default=SIFIR)
    teslimat_ucreti = models.DecimalField("teslimat ücreti", max_digits=10,
                                          decimal_places=2, default=SIFIR)
    toplam = models.DecimalField("toplam", max_digits=10, decimal_places=2, default=SIFIR)
    provizyon_tutari = models.DecimalField("bloke edilen", max_digits=10,
                                           decimal_places=2, default=SIFIR)
    cekilen_tutar = models.DecimalField("çekilen", max_digits=10, decimal_places=2,
                                        null=True, blank=True)

    durum = models.CharField("durum", max_length=15, choices=Durum.choices, default=Durum.ALINDI)
    odeme_durumu = models.CharField("ödeme", max_length=12, choices=OdemeDurumu.choices,
                                    default=OdemeDurumu.BEKLIYOR)
    musteri_notu = models.CharField("müşteri notu", max_length=300, blank=True)
    ic_not = models.TextField("iç not", blank=True,
                              help_text="Müşteriye görünmez.")

    test_siparisi = models.BooleanField(
        "deneme siparişi", default=False,
        help_text="Vitrin test modundayken verilen sipariş. Raporlarda sayılmaz.")

    kesildi_zamani = models.DateTimeField("kesim zamanı", null=True, blank=True)
    hazirlandi_zamani = models.DateTimeField("hazırlanma zamanı", null=True, blank=True)
    teslim_zamani = models.DateTimeField("teslim zamanı", null=True, blank=True)
    onay_zamani = models.DateTimeField("üye onayı", null=True, blank=True)

    class Meta:
        verbose_name = "sipariş"
        verbose_name_plural = "siparişler"
        ordering = ["-olusturuldu"]
        indexes = [
            models.Index(fields=["magaza", "durum"]),
            models.Index(fields=["teslim_takvimi", "durum"]),
        ]

    def __str__(self):
        return f"{self.numara} — {self.uye.ad_soyad}"

    # -- kurulum -----------------------------------------------------------
    @staticmethod
    def adres_kopyasi(adres):
        """Adres kaydından sipariş alanlarını üretir."""
        return {
            "teslim_ad_soyad": adres.kime,
            "teslim_telefon": adres.hangi_telefon,
            "teslim_acik_adres": adres.acik_adres,
            "teslim_mahalle": adres.mahalle.ad,
            "teslim_ilce": adres.mahalle.ilce.ad,
            "teslim_il": adres.mahalle.ilce.il.ad,
            "teslim_tarif": adres.tarif,
            "teslim_enlem": adres.enlem,
            "teslim_boylam": adres.boylam,
        }

    def save(self, *args, **kwargs):
        if not self.numara:
            self.numara = self.numara_uret()
        super().save(*args, **kwargs)

    @classmethod
    def numara_uret(cls):
        """BH-2026-001042 — yıl içinde artan sıra."""
        yil = timezone.localdate().year
        onek = f"BH-{yil}-"
        son = (cls.objects.filter(numara__startswith=onek)
               .order_by("-numara").values_list("numara", flat=True).first())
        sira = int(son.rsplit("-", 1)[1]) + 1 if son else 1
        return f"{onek}{sira:06d}"

    # -- tutar hesabı ------------------------------------------------------
    def tutarlari_hesapla(self, kaydet=False):
        """
        Satırlardan toplamları üretir.

        Teslim miktarı girilmişse onu, girilmemişse sipariş miktarını kullanır —
        yani tartımdan önce tahmini, sonra kesin tutarı verir.
        """
        ayarlar = SatisAyarlari.getir(self.magaza)
        ara = SIFIR
        provizyon = SIFIR
        for kalem in self.kalemler.all():
            ara += kalem.tutar
            provizyon += kalem.provizyon_tutari
        self.ara_toplam = kurus(ara)
        self.teslimat_ucreti = ayarlar.teslimat_ucreti_hesapla(self.ara_toplam)
        self.toplam = kurus(self.ara_toplam + self.teslimat_ucreti)
        if self.provizyon_tutari == SIFIR:
            # Provizyon sipariş anında belirlenir, sonra değişmez:
            # bankadan bloke edilen tutar bu.
            self.provizyon_tutari = kurus(provizyon + self.teslimat_ucreti)
        if kaydet:
            self.save(update_fields=["ara_toplam", "teslimat_ucreti", "toplam",
                                     "provizyon_tutari", "guncellendi"])
        return self.toplam

    # -- durum geçişleri ---------------------------------------------------
    @property
    def degistirilebilir_mi(self):
        """
        Müşteri siparişini değiştirebilir mi?

        Karar: kesim saatine kadar evet, sonra hayır. Kesim saatinin varlık sebebi
        alım listesini dondurmak; sonrasında değişikliğe izin vermek mağaza hale
        gittikten sonra listenin değişmesi demek.
        """
        if self.durum != self.Durum.ALINDI:
            return False
        if self.teslim_takvimi is None:
            return True          # kargo siparişinde kesim saati yok
        return self.teslim_takvimi.siparis_alinabilir

    @transaction.atomic
    def iptal_et(self, kullanici=None, sebep=""):
        """Siparişi iptal eder ve rezerve edilen stoğu geri verir."""
        if self.durum in (self.Durum.TESLIM_EDILDI, self.Durum.IPTAL):
            raise ValidationError("Bu sipariş iptal edilemez.")
        if not self.degistirilebilir_mi:
            raise ValidationError(
                "Kesim saati geçti, sipariş iptal edilemez. Mağazayla görüşün.")
        for kalem in self.kalemler.select_related("magaza_urun"):
            kalem.magaza_urun.stok_degistir(
                kalem.siparis_miktari, StokHareketi.Tur.IADE, kullanici=kullanici,
                aciklama=f"Sipariş iptali {self.numara}", takipsizse_atla=True)
        self.durum = self.Durum.IPTAL
        if sebep:
            self.ic_not = f"{self.ic_not}\nİptal: {sebep}".strip()
        self.save(update_fields=["durum", "ic_not", "guncellendi"])

    def kesildi_isaretle(self):
        if self.durum == self.Durum.ALINDI:
            self.durum = self.Durum.KESILDI
            self.kesildi_zamani = timezone.now()
            self.save(update_fields=["durum", "kesildi_zamani", "guncellendi"])

    def teslim_edildi_isaretle(self):
        self.durum = self.Durum.TESLIM_EDILDI
        self.teslim_zamani = timezone.now()
        self.save(update_fields=["durum", "teslim_zamani", "guncellendi"])

    # -- özetler -----------------------------------------------------------
    @property
    def eksik_kalemler(self):
        """Bulunamayan ya da eksik giden satırlar."""
        return [k for k in self.kalemler.all() if k.eksik_mi]

    @property
    def otomatik_onay_zamani(self):
        """Üye onay vermezse ne zaman onaylanmış sayılır?"""
        if self.teslim_zamani is None:
            return None
        saat = SatisAyarlari.getir(self.magaza).otomatik_teslim_onayi_saat
        return self.teslim_zamani + timezone.timedelta(hours=saat)


class SiparisKalemi(ZamanDamgali):
    """
    Siparişteki bir satır. Ürün adı, birimi ve fiyatı **kopyalanmıştır**.

    İki miktar tutuluyor:
      siparis_miktari → müşterinin istediği
      teslim_miktari  → gerçekte giden (tartım sonrası, ya da bulunamadıysa 0)

    Para `teslim_miktari` üzerinden çekilir. Henüz tartılmadıysa sipariş miktarı
    kullanılır, yani tahmini tutar görünür.
    """

    class Durum(models.TextChoices):
        BEKLIYOR = "bekliyor", "Bekliyor"
        HAZIR = "hazir", "Hazırlandı"
        BULUNAMADI = "bulunamadi", "Bulunamadı"

    siparis = models.ForeignKey(Siparis, on_delete=models.CASCADE,
                                related_name="kalemler", verbose_name="sipariş")
    magaza_urun = models.ForeignKey(MagazaUrun, on_delete=models.PROTECT,
                                    related_name="siparis_kalemleri", verbose_name="ürün")

    # kopyalanan bilgiler
    urun_adi = models.CharField("ürün", max_length=140)
    birim_adi = models.CharField("birim", max_length=12)
    tartili_mi = models.BooleanField("tartılı", default=False)
    birim_fiyat = models.DecimalField("birim fiyat", max_digits=10, decimal_places=2)

    siparis_miktari = models.DecimalField("sipariş miktarı", max_digits=10, decimal_places=3)
    teslim_miktari = models.DecimalField(
        "teslim miktarı", max_digits=10, decimal_places=3, null=True, blank=True,
        help_text="Tartımdan sonra girilir. Ürün bulunamadıysa 0 yazılır.")
    durum = models.CharField("durum", max_length=12, choices=Durum.choices,
                             default=Durum.BEKLIYOR)
    not_metni = models.CharField("not", max_length=200, blank=True)

    class Meta:
        verbose_name = "sipariş kalemi"
        verbose_name_plural = "sipariş kalemleri"
        ordering = ["urun_adi"]
        unique_together = [("siparis", "magaza_urun")]

    def __str__(self):
        return f"{self.urun_adi} × {self.gecerli_miktar}"

    @property
    def gecerli_miktar(self):
        """Tartıldıysa teslim miktarı, tartılmadıysa sipariş miktarı."""
        return self.siparis_miktari if self.teslim_miktari is None else self.teslim_miktari

    @property
    def tutar(self):
        return kurus(self.birim_fiyat * self.gecerli_miktar)

    @property
    def provizyon_tutari(self):
        """Tampon yalnızca tartılı kaleme uygulanır."""
        tahmini = kurus(self.birim_fiyat * self.siparis_miktari)
        if not self.tartili_mi:
            return tahmini
        return SatisAyarlari.getir(self.siparis.magaza).provizyon_tutari(tahmini)

    @property
    def eksik_mi(self):
        return (self.teslim_miktari is not None
                and self.teslim_miktari < self.siparis_miktari)

    @property
    def bulunamadi_mi(self):
        return self.teslim_miktari is not None and self.teslim_miktari == 0

    @property
    def fark_tutari(self):
        """Sipariş ile teslim arasındaki tutar farkı (eksi = müşteri daha az ödüyor)."""
        if self.teslim_miktari is None:
            return SIFIR
        return kurus(self.birim_fiyat * (self.teslim_miktari - self.siparis_miktari))

    @transaction.atomic
    def tartim_gir(self, miktar, kullanici=None):
        """
        Paketleme ekranından tartım girilir.

        Stok sipariş anında sipariş miktarı kadar düşülmüştü; aradaki fark
        burada **tartı farkı** olarak deftere yazılır. Sayım düzeltmesi değil:
        tartı farkı normal işleyişin parçası, defteri yanıltmasın.
        """
        miktar = Decimal(str(miktar))
        if miktar < 0:
            raise ValidationError("Teslim miktarı eksi olamaz.")
        onceki = self.teslim_miktari
        self.teslim_miktari = miktar
        self.durum = self.Durum.BULUNAMADI if miktar == 0 else self.Durum.HAZIR
        self.save(update_fields=["teslim_miktari", "durum", "guncellendi"])

        temel = self.siparis_miktari if onceki is None else onceki
        fark = temel - miktar          # eksik çıktıysa artı: stoğa geri döner
        if fark != 0:
            self.magaza_urun.stok_degistir(
                fark, StokHareketi.Tur.TARTI_FARKI, kullanici=kullanici,
                aciklama=f"{self.siparis.numara} · {self.urun_adi}",
                takipsizse_atla=True)
        self.siparis.tutarlari_hesapla(kaydet=True)
        return self


# ==========================================================================
# ALIM LİSTESİ
# ==========================================================================
def alim_listesi(magaza, tarih):
    """
    Kesim sonrası alım listesi: o gün hangi üründen kaç birim alınacak.

    Bu işin kalbi. Mağaza bu listeyle hale gidiyor; listede olmayan ürün
    alınmıyor, fazlası alınmıyor. "Önce talep, sonra alım" bu fonksiyonda
    somutlaşıyor.

    Model olarak saklamıyoruz: siparişlerden her seferinde hesaplanıyor, yani
    bir sipariş iptal edilirse liste kendiliğinden doğru kalıyor. Saklasaydık
    güncel tutmak ayrı bir iş olurdu.

    Dönen satırlar: ürün, birim, toplam miktar, sipariş sayısı, tahmini tutar.
    """
    kalemler = (SiparisKalemi.objects
                .filter(siparis__magaza=magaza,
                        siparis__teslim_takvimi__tarih=tarih,
                        siparis__test_siparisi=False)
                .exclude(siparis__durum=Siparis.Durum.IPTAL)
                .values("magaza_urun", "urun_adi", "birim_adi")
                .annotate(toplam_miktar=models.Sum("siparis_miktari"),
                          siparis_sayisi=models.Count("siparis", distinct=True),
                          tahmini_tutar=models.Sum(
                              models.F("siparis_miktari") * models.F("birim_fiyat"),
                              output_field=models.DecimalField(max_digits=12, decimal_places=2)))
                .order_by("urun_adi"))
    return list(kalemler)


@transaction.atomic
def gunu_kes(teslim_takvimi):
    """
    Teslim gününü keser: sipariş almayı kapatır, siparişleri KESILDI yapar.

    Kesim saatinde kendiliğinden çalışacak (zamanlanmış görev), ama mağaza
    yöneticisi panelden erken de kesebilir — kapasite dolduğunda işe yarar.
    """
    if teslim_takvimi.durum != TeslimTakvimi.Durum.ACIK:
        raise ValidationError("Bu gün zaten kesilmiş ya da kapalı.")
    teslim_takvimi.durum = TeslimTakvimi.Durum.KESILDI
    teslim_takvimi.save(update_fields=["durum", "guncellendi"])

    siparisler = teslim_takvimi.siparisler.filter(durum=Siparis.Durum.ALINDI)
    adet = 0
    for siparis in siparisler:
        siparis.kesildi_isaretle()
        adet += 1
    return adet
