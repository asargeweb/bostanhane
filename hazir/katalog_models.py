"""
Bostanhane — katalog uygulaması modelleri

Bu dosya `katalog/models.py` yerine geçer.

Üç model var ve ayrımları önemli:

  Kategori     → "Sebze", "Yeşillik", "Yöresel ürün"
  Urun         → ürünün **kendisi**: domates nedir, kilogramla mı satılır,
                 tartılı mı, hangi kanallarda satılabilir, raf ömrü ne
  MagazaUrun   → o ürünün **bir mağazadaki hali**: fiyatı, stok durumu,
                 satışta mı

**Neden ürün ile mağaza fiyatı ayrı?** Domates Beyşehir'de 24 ₺, Karaman'da 27 ₺
olabilir; biri bugün tükenmişken diğerinde bulunabilir. Ürünün tanımı (birim,
tartılı mı, raf ömrü) her yerde aynıdır, fiyatı ve stoğu değildir. Mahalle ile
HizmetMahallesi ayrımının aynısı.

Fiyatsız ürün kaydedilebilir ama **satışa açılamaz**: `aktif` işaretlemek için
fiyat zorunlu. Böylece listeyi fiyatsız içeri alıp fiyatları panelden tek tek
girebiliyoruz.
"""

from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models, transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from core.models import ZamanDamgali


class Birim(ZamanDamgali):
    """
    Satış birimi: kilogram, adet, demet, kavanoz…

    Sabit liste değil tablo: "tepsi" ya da "kasa" gerektiğinde panelden eklensin,
    kod değişmesin. İlk yedi birimi migration açar.
    """

    # Gram gösterimi ve tartılı ürün kuralı kilogramı kısa yazılışından tanır.
    KILOGRAM = "kg"

    ad = models.CharField("birim adı", max_length=40, unique=True,
                          help_text="Örnek: Kilogram, Demet, Kavanoz.")
    kisaltma = models.CharField("kısa yazılış", max_length=12, unique=True,
                                help_text="Listede ve fiyatın yanında görünür. Örnek: kg, demet.")
    kesirli = models.BooleanField(
        "kesirli satılır", default=False,
        help_text="İşaretliyse 0,5 gibi kesirli miktarla satılır (kilogram gibi). "
                  "Tartılı ürün yalnızca kesirli birimle satılabilir.")
    sira = models.PositiveIntegerField("sıra", default=0)
    aktif = models.BooleanField("aktif", default=True,
                                help_text="Kapalıysa yeni üründe seçilemez; eski ürünler etkilenmez.")

    class Meta:
        verbose_name = "birim"
        verbose_name_plural = "birimler"
        ordering = ["sira", "ad"]

    def __str__(self):
        return self.ad

    @property
    def kilogram_mi(self):
        return self.kisaltma == self.KILOGRAM


# Kargoya uygunluk eşiği: oda sıcaklığında en az bu kadar gün dayanmalı.
KARGO_ASGARI_RAF_OMRU = 14


class Kategori(ZamanDamgali):
    """Sitede ürünlerin gruplandığı başlık."""

    ad = models.CharField("kategori", max_length=80, unique=True)
    slug = models.SlugField("kısa ad", max_length=100, unique=True)
    aciklama = models.CharField("açıklama", max_length=200, blank=True)
    gorsel = models.ImageField("görsel", upload_to="kategori/", blank=True)
    sira = models.PositiveIntegerField("sıra", default=0)
    aktif = models.BooleanField("aktif", default=True)

    class Meta:
        verbose_name = "kategori"
        verbose_name_plural = "kategoriler"
        ordering = ["sira", "ad"]

    def __str__(self):
        return self.ad

    @property
    def urun_sayisi(self):
        return self.urunler.filter(aktif=True).count()


class Urun(ZamanDamgali):
    """
    Ürünün kendisi. Fiyat burada değil; fiyat `MagazaUrun`'da.

    `tartili_mi` alanı işin kalbine dokunuyor: evet ise sepette provizyon alınır
    (tahmini tutar + tampon), kesin tutar tartımdan sonra çekilir.
    """

    kategori = models.ForeignKey(Kategori, on_delete=models.PROTECT,
                                 related_name="urunler", verbose_name="kategori")
    ad = models.CharField("ürün adı", max_length=140)
    slug = models.SlugField("kısa ad", max_length=160, unique=True)
    aciklama = models.TextField("açıklama", blank=True,
                                help_text="Ürün kartında görünür. Nereden geldiği, nasıl saklanacağı.")
    gorsel = models.ImageField("görsel", upload_to="urun/", blank=True)

    # -- satış biçimi ------------------------------------------------------
    birim = models.ForeignKey(Birim, on_delete=models.PROTECT, related_name="urunler",
                              verbose_name="birim", limit_choices_to={"aktif": True})
    tartili_mi = models.BooleanField(
        "tartılı ürün", default=True,
        help_text="İşaretliyse sepette provizyon alınır, kesin tutar tartımdan sonra çekilir.")
    satis_adimi = models.DecimalField(
        "satış adımı", max_digits=7, decimal_places=3, default=Decimal("1.000"),
        validators=[MinValueValidator(Decimal("0.001"))],
        help_text="Birim cinsinden en küçük artırma miktarı. Kilogramda 0,500 = 500 g.")
    ambalaj_bilgisi = models.CharField(
        "ambalaj", max_length=40, blank=True,
        help_text="Ambalajlı üründe içindekinin miktarı. Örnek: 850 g, 1 L.")

    # -- satış kanalları ---------------------------------------------------
    yerel_satis = models.BooleanField("yerel teslimat", default=True,
                                      help_text="Mahalle teslimatında satılır.")
    kargo_satis = models.BooleanField(
        "kargo", default=False,
        help_text="Kargoyla tüm Türkiye'ye gönderilir. Dört şart birden sağlanmalı — "
                  "aşağıdaki denetim bunu kontrol eder.")
    kurumsal_satis = models.BooleanField("kurumsal (B2B)", default=True)
    abonelige_uygun = models.BooleanField(
        "aboneliğe uygun", default=False,
        help_text="Düzenli, tekrarlayan siparişe açılabilir mi. (Abonelik modülü sonra gelecek.)")

    # -- saklama ve uyarı --------------------------------------------------
    raf_omru_gun = models.PositiveIntegerField(
        "raf ömrü (gün)", null=True, blank=True,
        help_text="Uygun koşulda kaç gün dayanır. Kargo kararının dayanağı.")
    soguk_zincir = models.BooleanField(
        "soğuk zincir gerekir", default=False,
        help_text="0–4 °C'de taşınmalı. Paketleme ve kurye ekranında uyarı çıkar.")
    mevsim = models.CharField("mevsim", max_length=60, blank=True,
                             help_text="Örnek: Haziran–Ekim, Tüm yıl.")
    uyari_metni = models.CharField(
        "uyarı metni", max_length=200, blank=True,
        help_text="Ürün kartında ve etikette görünür. Örnek: Kullanmadan önce yıkayınız.")

    sira = models.PositiveIntegerField("sıra", default=0)
    aktif = models.BooleanField("aktif", default=True,
                                help_text="Kapalıysa hiçbir mağazada görünmez.")

    class Meta:
        verbose_name = "ürün"
        verbose_name_plural = "ürünler"
        ordering = ["kategori__sira", "sira", "ad"]

    def __str__(self):
        return self.ad

    # -- görünüm yardımcıları ---------------------------------------------
    @property
    def birim_metni(self):
        return self.birim.ad

    @property
    def satis_adimi_metni(self):
        """'kilogram · 500 g'dan itibaren' gibi okunur metin."""
        if self.birim.kilogram_mi:
            adim = self.satis_adimi
            if adim < 1:
                gram = int(adim * 1000)
                return f"{self.birim_metni.lower()} · {gram} g'dan itibaren"
            return f"{self.birim_metni.lower()} · {adim.normalize()} kg'dan itibaren"
        tekil = self.birim_metni.lower()
        if self.satis_adimi == 1:
            return f"1 {tekil}"
        return f"{self.satis_adimi.normalize()} {tekil}"

    @property
    def kanallar_metni(self):
        acik = []
        if self.yerel_satis:
            acik.append("Yerel")
        if self.kargo_satis:
            acik.append("Kargo")
        if self.kurumsal_satis:
            acik.append("Kurumsal")
        return " · ".join(acik) if acik else "—"

    @property
    def provizyon_gerekir(self):
        """Tartılı üründe sipariş anında kesin tutar bilinmez; provizyon alınır."""
        return self.tartili_mi

    # -- iş kuralı denetimi ------------------------------------------------
    def clean(self):
        """
        Kargo kanalının dört şartını burada uyguluyoruz. Panelde yanlışlıkla
        kargoya açılan çabuk bozulan bir ürün, müşteriye bozuk mal gitmesi demek —
        bu yüzden kural kodda duruyor, sadece belgede değil.
        """
        super().clean()
        hatalar = {}

        if self.kargo_satis:
            if self.tartili_mi:
                hatalar["kargo_satis"] = (
                    "Tartılı ürün kargoyla gönderilemez: sabit ağırlıklı ambalaj gerekir. "
                    "Ya tartılı işaretini kaldırın ya kargoyu kapatın.")
            if self.soguk_zincir:
                hatalar["kargo_satis"] = (
                    "Soğuk zincir gerektiren ürün kargoyla gönderilemez.")
            if self.raf_omru_gun is None:
                hatalar["raf_omru_gun"] = (
                    "Kargoya açılan ürünün raf ömrü girilmeli.")
            elif self.raf_omru_gun < KARGO_ASGARI_RAF_OMRU:
                hatalar["raf_omru_gun"] = (
                    f"Kargo için raf ömrü en az {KARGO_ASGARI_RAF_OMRU} gün olmalı; "
                    f"bu ürün {self.raf_omru_gun} gün.")

        if self.birim_id:
            if self.tartili_mi and not self.birim.kesirli:
                hatalar["tartili_mi"] = (
                    "Tartılı ürün kesirli bir birimle (kilogram gibi) satılır. Birimi "
                    "değiştirin ya da tartılı işaretini kaldırın.")
            if not self.birim.kesirli and self.satis_adimi % 1:
                hatalar["satis_adimi"] = (
                    f"{self.birim.ad} kesirli satılmaz; satış adımı tam sayı olmalı.")

        if hatalar:
            raise ValidationError(hatalar)


class MagazaUrun(ZamanDamgali):
    """Bir ürünün bir mağazadaki fiyatı ve stok durumu."""

    class Durum(models.TextChoices):
        SATISTA = "satista", "Satışta"
        TUKENDI = "tukendi", "Tükendi"
        MEVSIM_DISI = "mevsim_disi", "Mevsim dışı"

    magaza = models.ForeignKey("core.Magaza", on_delete=models.CASCADE,
                               related_name="urunler", verbose_name="mağaza")
    urun = models.ForeignKey(Urun, on_delete=models.CASCADE,
                             related_name="magaza_kayitlari", verbose_name="ürün")
    fiyat = models.DecimalField(
        "fiyat (₺)", max_digits=10, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(Decimal("0.01"))],
        help_text="Birim başına satış fiyatı. Boşken ürün satışa açılamaz.")
    eski_fiyat = models.DecimalField(
        "eski fiyat (₺)", max_digits=10, decimal_places=2, null=True, blank=True,
        help_text="Doluysa üstü çizili gösterilir. İndirim için.")
    durum = models.CharField("durum", max_length=12, choices=Durum.choices, default=Durum.SATISTA)
    gunluk_limit = models.PositiveIntegerField(
        "günlük satış limiti", null=True, blank=True,
        help_text="Bir teslim gününde en fazla kaç birim satılsın. Boşsa sınırsız.")
    # Taze üründe stok boş kalır: önce talep toplanır, sonra alınır (iş modelinin
    # temeli). Stok yalnızca depoda bekleyen ürün (bal, bakliyat, yumurta) için tutulur.
    stok = models.DecimalField(
        "stok", max_digits=10, decimal_places=3, null=True, blank=True,
        help_text="Boşsa stok takip edilmez (sınırsız). Yalnızca stok hareketiyle değişir: "
                  "Ürünler listesindeki “ekle / çıkar” ile.")
    sira = models.PositiveIntegerField("sıra", default=0)
    aktif = models.BooleanField("satışta", default=False,
                               help_text="Fiyat girilmeden açılamaz.")

    class Meta:
        verbose_name = "mağaza ürünü"
        verbose_name_plural = "mağaza ürünleri"
        ordering = ["magaza__ad", "urun__kategori__sira", "sira", "urun__ad"]
        unique_together = [("magaza", "urun")]

    def __str__(self):
        return f"{self.urun.ad} — {self.magaza.ad}"

    # -- yardımcılar -------------------------------------------------------
    @property
    def satista_mi(self):
        return (self.aktif and self.fiyat is not None
                and self.durum == self.Durum.SATISTA and self.urun.aktif
                and self.stok_yeterli_mi(self.urun.satis_adimi))

    # -- stok ----------------------------------------------------------------
    def stok_yeterli_mi(self, miktar):
        """Takip edilmeyen (boş) stok sınırsız sayılır."""
        return self.stok is None or self.stok >= Decimal(str(miktar))

    def stok_degistir(self, miktar, tur, kullanici=None, aciklama="", takipsizse_atla=False):
        """
        Stoğu `miktar` kadar değiştirir (giriş artı, çıkış eksi) ve deftere yazar.

        Stok rakamını doğrudan değiştirmek yerine her değişimi bir hareket olarak
        tutuyoruz: "bu 10 kg nereden geldi, 2 kg nereye gitti" sorusunun cevabı
        defterde kalsın. Satır kilitlenir; aynı anda iki satış stoğu eksiye düşüremez.

        Takip edilmeyen üründe mal kabul takibi başlatır (0'dan sayar).
        `takipsizse_atla` satış içindir: takipsiz üründe satış stoğa dokunmaz.
        """
        miktar = Decimal(str(miktar))
        with transaction.atomic():
            kayit = MagazaUrun.objects.select_for_update().get(pk=self.pk)
            onceki = kayit.stok
            if onceki is None and takipsizse_atla:
                return None
            sonraki = (onceki or Decimal("0")) + miktar
            if sonraki < 0:
                def yaz(sayi):
                    return f"{Decimal(sayi).normalize():f}".replace(".", ",")
                raise ValidationError(
                    f"Stok yetmiyor: {yaz(onceki or 0)} var, {yaz(abs(miktar))} çıkarılmak istendi.")
            kayit.stok = sonraki
            kayit.save(update_fields=["stok", "guncellendi"])
            hareket = StokHareketi.objects.create(
                magaza_urun=kayit, tur=tur, miktar=miktar, onceki_stok=onceki,
                sonraki_stok=sonraki, aciklama=aciklama, kullanici=kullanici)
        self.stok = sonraki
        return hareket

    def stok_dus(self, miktar, kullanici=None, aciklama=""):
        """Satışta çağrılır (Adım 5 — sipariş). Takipsiz üründe hiçbir şey yapmaz."""
        return self.stok_degistir(-Decimal(str(miktar)), StokHareketi.Tur.SATIS,
                                  kullanici=kullanici, aciklama=aciklama, takipsizse_atla=True)

    def stok_takibini_kapat(self, kullanici=None):
        """Stoğu boşaltır (sınırsız yapar); kapanış da deftere yazılır."""
        with transaction.atomic():
            kayit = MagazaUrun.objects.select_for_update().get(pk=self.pk)
            if kayit.stok is None:
                return None
            onceki = kayit.stok
            kayit.stok = None
            kayit.save(update_fields=["stok", "guncellendi"])
            hareket = StokHareketi.objects.create(
                magaza_urun=kayit, tur=StokHareketi.Tur.TAKIP_KAPATILDI,
                miktar=-onceki, onceki_stok=onceki, sonraki_stok=None, kullanici=kullanici)
        self.stok = None
        return hareket

    @property
    def indirimli_mi(self):
        return bool(self.eski_fiyat and self.fiyat and self.eski_fiyat > self.fiyat)

    @property
    def indirim_orani(self):
        if not self.indirimli_mi:
            return 0
        return round((self.eski_fiyat - self.fiyat) / self.eski_fiyat * 100)

    def tutar(self, miktar):
        """Verilen miktar için satır tutarı. Fiyat yoksa None."""
        if self.fiyat is None:
            return None
        return (self.fiyat * Decimal(str(miktar))).quantize(Decimal("0.01"))

    def provizyon_tutari(self, miktar):
        """
        Tartılı üründe karttan bloke edilecek tutar: tahmini tutar + tampon.

        Tartıda eksik çıkarsa fazlası serbest bırakılır, fazla çıkarsa tampon
        içinde kalındığı sürece ek çekim gerekmez.

        Tampon oranı mağazanın **satış ayarlarından** okunur (panelden
        düzenlenebilir), ayar kaydı yoksa kendiliğinden varsayılanlarla açılır.
        """
        tahmini = self.tutar(miktar)
        if tahmini is None:
            return None
        if not self.urun.tartili_mi:
            return tahmini
        # Döngüsel içe alma olmasın diye burada çağırıyoruz.
        from core.models import SatisAyarlari
        return SatisAyarlari.getir(self.magaza).provizyon_tutari(tahmini)

    def clean(self):
        super().clean()
        if self.aktif and self.fiyat is None:
            raise ValidationError({
                "fiyat": "Ürünü satışa açmak için fiyat girilmeli."
            })
        if self.eski_fiyat and self.fiyat and self.eski_fiyat <= self.fiyat:
            raise ValidationError({
                "eski_fiyat": "Eski fiyat, yeni fiyattan büyük olmalı. "
                              "İndirim yoksa bu alanı boş bırakın."
            })



class StokHareketi(ZamanDamgali):
    """
    Stoğun her değişimi bir satır: mal kabul, fire, sayım, satış, iade.

    Kayıtlar düzeltilmez, silinmez: yanlış giriş ters bir hareketle (sayım
    düzeltmesi) dengelenir. Böylece defter her zaman stoğun açıklaması olur.
    """

    class Tur(models.TextChoices):
        MAL_KABUL = "mal_kabul", "Mal kabul"
        FIRE = "fire", "Fire"
        SAYIM = "sayim", "Sayım düzeltmesi"
        SATIS = "satis", "Satış"
        TARTI_FARKI = "tarti_farki", "Tartı farkı"
        IADE = "iade", "İade"
        TAKIP_KAPATILDI = "takip_kapatildi", "Takip kapatıldı"

    magaza_urun = models.ForeignKey(MagazaUrun, on_delete=models.CASCADE,
                                    related_name="stok_hareketleri", verbose_name="mağaza ürünü")
    tur = models.CharField("tür", max_length=16, choices=Tur.choices)
    miktar = models.DecimalField("miktar", max_digits=10, decimal_places=3,
                                 help_text="Giriş artı, çıkış eksi.")
    onceki_stok = models.DecimalField("önceki stok", max_digits=10, decimal_places=3,
                                      null=True, blank=True)
    sonraki_stok = models.DecimalField("sonraki stok", max_digits=10, decimal_places=3,
                                       null=True, blank=True)
    aciklama = models.CharField("açıklama", max_length=200, blank=True)
    kullanici = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                  null=True, blank=True, related_name="+", verbose_name="kim")

    class Meta:
        verbose_name = "stok hareketi"
        verbose_name_plural = "stok hareketleri"
        ordering = ["-olusturuldu", "-pk"]

    def __str__(self):
        return f"{self.magaza_urun.urun.ad}: {self.miktar:+} ({self.get_tur_display()})"


@receiver(post_save, sender=Urun)
def urunu_magazalara_ac(sender, instance, created, **kwargs):
    """
    Yeni ürün tanımlanınca her aktif mağazaya **fiyatsız ve kapalı** bir kayıt açar.

    Neden: panelde ürün ekleyen biri, ürünün ayrıca "Mağaza ürünleri" listesine de
    eklenmesi gerektiğini bilmek zorunda kalmasın. Ürünü ekle, fiyatını yaz, aç —
    o kadar. Kayıt kapalı açılıyor, yani fiyat girilmeden kimseye görünmüyor.

    Mağaza sonradan açılırsa (Karaman) var olan ürünler için "Seçili ürünleri bütün
    mağazalara ekle" işlemi kullanılır.
    """
    if not created:
        return
    from core.models import Magaza

    for magaza in Magaza.objects.filter(aktif=True):
        MagazaUrun.objects.get_or_create(magaza=magaza, urun=instance)
