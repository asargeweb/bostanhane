"""
Bostanhane — core uygulaması modelleri

Bu dosya `core/models.py` yerine geçer.

İki ayrı şey var ve ayrı olmaları önemli:

**Coğrafya** — resmî idari yapı. Değişmez, herkes için aynıdır:
    Il → Ilce → Mahalle        "Konya → Beyşehir → Müftü Mahallesi"

**Hizmet alanı** — hangi mağaza hangi mahalleye gidiyor, kaç siparişe kadar:
    Magaza → HizmetMahallesi → HaftalikTeslimGunu → TeslimTakvimi

Neden ayrı? Çünkü üyenin adresi Türkiye'nin her yerinde olabilir (kargo kanalı),
ama yerel teslimat yalnızca mağazanın gittiği mahallelerde vardır. Adres coğrafi
mahalleye bağlanır; o mahallede aktif bir HizmetMahallesi kaydı varsa yerel
teslimat açıktır, yoksa yalnızca kargo seçeneği görünür.

Zincirin son iki halkası:
    HaftalikTeslimGunu → *kural*:      "Müftü salı ve cuma, kesim 1 gün önce 18:00"
    TeslimTakvimi      → *somut gün*:  "3 Ekim Cuma, kapasite 45, durum açık"

Kural ile takvim neden ayrı? Hayat kuralı bozar: bayram olur, araç arızalanır,
kapasite dolar. Takvim kaydı sayesinde tek bir gün kapatılabilir, kapasitesi
değiştirilebilir; haftalık kural bozulmaz. **Siparişler TeslimTakvimi'ne bağlanır.**
"""

from datetime import datetime, timedelta, time
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone


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


# ==========================================================================
# COĞRAFYA — resmî idari yapı
# ==========================================================================
class Il(models.Model):
    """81 il. `cografya_yukle` komutu doldurur; elle girilmesi gerekmez."""

    ad = models.CharField("il", max_length=40, unique=True)
    slug = models.SlugField("kısa ad", max_length=50, unique=True)
    plaka = models.PositiveSmallIntegerField("plaka kodu", unique=True)

    class Meta:
        verbose_name = "il"
        verbose_name_plural = "iller"
        ordering = ["ad"]

    def __str__(self):
        return self.ad

    @property
    def ilce_sayisi(self):
        return self.ilceler.count()


class Ilce(models.Model):
    """İlçe. Şimdilik yalnızca Konya ve Karaman ilçeleri yüklü."""

    il = models.ForeignKey(Il, on_delete=models.CASCADE,
                           related_name="ilceler", verbose_name="il")
    ad = models.CharField("ilçe", max_length=60)
    slug = models.SlugField("kısa ad", max_length=70)

    class Meta:
        verbose_name = "ilçe"
        verbose_name_plural = "ilçeler"
        ordering = ["il__ad", "ad"]
        unique_together = [("il", "slug")]

    def __str__(self):
        return f"{self.ad} / {self.il.ad}"

    @property
    def mahalle_sayisi(self):
        return self.mahalleler.count()


class Mahalle(models.Model):
    """
    Resmî mahalle.

    6360 sayılı kanunla büyükşehir ilçelerinde köyler de mahalleye dönüştü;
    bu yüzden `tip` alanı merkez mahallesi ile köy kökenli mahalleyi ayırıyor.
    Pilot çalışma merkez mahallelerinde yürüyecek, kırsal mahalleler sonra.
    """

    class Tip(models.TextChoices):
        MERKEZ = "merkez", "Merkez mahallesi"
        KIRSAL = "kirsal", "Köy kökenli mahalle"

    ilce = models.ForeignKey(Ilce, on_delete=models.CASCADE,
                             related_name="mahalleler", verbose_name="ilçe")
    ad = models.CharField("mahalle", max_length=120)
    slug = models.SlugField("kısa ad", max_length=140)
    tip = models.CharField("tip", max_length=10, choices=Tip.choices, default=Tip.MERKEZ)
    posta_kodu = models.CharField("posta kodu", max_length=5, blank=True)

    # Nüfus iki kararı besliyor: hangi mahalleye önce gidilecek ve günlük
    # kapasite ne olmalı. 10.000 kişilik Yeni ile 300 kişilik Adaköy aynı
    # kapasiteyle planlanamaz.
    #
    # Kaynak ve yıl alanları bilerek var: nüfus her yıl değişiyor ve bu sayılar
    # bizim ölçümümüz değil. "Bu rakam nereden geldi" sorusunun cevabı kayıtta
    # dursun ki eskidiğinde fark edilsin.
    nufus = models.PositiveIntegerField("nüfus", null=True, blank=True)
    nufus_yili = models.PositiveSmallIntegerField("nüfus yılı", null=True, blank=True)
    nufus_kaynagi = models.CharField("nüfus kaynağı", max_length=120, blank=True,
                                     help_text="Örnek: TÜİK ADNKS 2023")

    class Meta:
        verbose_name = "mahalle"
        verbose_name_plural = "mahalleler"
        ordering = ["ilce__il__ad", "ilce__ad", "ad"]
        unique_together = [("ilce", "slug")]

    def __str__(self):
        return f"{self.ad} — {self.ilce.ad}"

    @property
    def il(self):
        return self.ilce.il

    @property
    def tam_ad(self):
        return f"{self.ad}, {self.ilce.ad}/{self.ilce.il.ad}"

    def yerel_hizmet(self):
        """Bu mahalleye giden aktif hizmet kaydı. None dönerse yerel teslimat yok."""
        return self.hizmet_kayitlari.filter(aktif=True).select_related("magaza").first()


# ==========================================================================
# HİZMET ALANI — hangi mağaza nereye gidiyor
# ==========================================================================
class Magaza(ZamanDamgali):
    """Bir şube. Aynı zamanda ürünlerin tartılıp paketlendiği butik depodur."""

    ad = models.CharField("mağaza adı", max_length=120, help_text="Örnek: Bostanhane Beyşehir")
    slug = models.SlugField("kısa ad", max_length=140, unique=True,
                            help_text="Adreste görünecek hali. Örnek: beysehir")
    il = models.ForeignKey(Il, on_delete=models.PROTECT,
                           related_name="magazalar", verbose_name="il")
    ilce = models.ForeignKey(Ilce, on_delete=models.PROTECT,
                             related_name="magazalar", verbose_name="ilçe")
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

    @property
    def konum(self):
        return f"{self.ilce.ad}, {self.il.ad}"


class HizmetMahallesi(ZamanDamgali):
    """
    "Bostanhane Beyşehir, Müftü Mahallesi'ne gidiyor; günde 45 siparişe kadar."

    Mağaza ile mahalle arasındaki bağ. Teslim günleri ve kapasite buraya bağlıdır,
    coğrafi mahalleye değil — çünkü aynı mahalleye ileride başka bir mağaza da
    hizmet verebilir ve her mağazanın kendi günü, kendi kapasitesi olur.
    """

    magaza = models.ForeignKey(Magaza, on_delete=models.CASCADE,
                               related_name="hizmet_mahalleleri", verbose_name="mağaza")
    mahalle = models.ForeignKey(Mahalle, on_delete=models.PROTECT,
                                related_name="hizmet_kayitlari", verbose_name="mahalle")
    gunluk_kapasite = models.PositiveIntegerField(
        "günlük teslimat kapasitesi", default=40,
        help_text="Bir teslim gününde kaç siparişe kadar alınabilir.")
    sira = models.PositiveIntegerField("sıra", default=0,
                                       help_text="Listelerde görünme sırası.")
    aktif = models.BooleanField("aktif", default=True,
                                help_text="Kapalıysa bu mahallede yerel teslimat görünmez.")

    class Meta:
        verbose_name = "hizmet verilen mahalle"
        verbose_name_plural = "hizmet verilen mahalleler"
        ordering = ["magaza__ad", "sira", "mahalle__ad"]
        unique_together = [("magaza", "mahalle")]

    def __str__(self):
        return f"{self.mahalle.ad} — {self.magaza.ad}"

    @property
    def ad(self):
        """Şablonlarda mahalle adı gibi davranabilsin."""
        return self.mahalle.ad

    @property
    def il(self):
        return self.mahalle.ilce.il

    @property
    def ilce(self):
        return self.mahalle.ilce

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

    hizmet_mahallesi = models.ForeignKey(
        HizmetMahallesi, on_delete=models.CASCADE,
        related_name="haftalik_gunler", verbose_name="hizmet verilen mahalle")
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
        ordering = ["hizmet_mahallesi", "gun"]
        unique_together = [("hizmet_mahallesi", "gun")]

    def __str__(self):
        return f"{self.hizmet_mahallesi.mahalle.ad} — {self.get_gun_display()}"

    def gecerli_kapasite(self):
        return self.kapasite or self.hizmet_mahallesi.gunluk_kapasite


class TeslimTakvimi(ZamanDamgali):
    """Belirli bir tarihteki somut teslimat. Siparişler buna bağlanır."""

    class Durum(models.TextChoices):
        ACIK = "acik", "Açık"
        KESILDI = "kesildi", "Kesildi"
        TAMAMLANDI = "tamamlandi", "Tamamlandı"
        IPTAL = "iptal", "İptal"

    hizmet_mahallesi = models.ForeignKey(
        HizmetMahallesi, on_delete=models.CASCADE,
        related_name="takvim", verbose_name="hizmet verilen mahalle")
    tarih = models.DateField("teslim tarihi")
    kesim_zamani = models.DateTimeField("kesim zamanı")
    kapasite = models.PositiveIntegerField("kapasite", default=40)
    durum = models.CharField("durum", max_length=12, choices=Durum.choices, default=Durum.ACIK)
    aciklama = models.CharField("not", max_length=200, blank=True)
    # Rotayı hangi kurye götürüyor. Boşsa mağazanın bütün kuryeleri görür —
    # tek kuryeyle çalışırken atama yapmak gereksiz iş olur.
    #
    # Atama mahalle-gün bazında, sipariş bazında değil: kurye bir mahalleyi
    # baştan sona dolaşır, tek tek siparişler bölüştürülmez.
    #
    # "kurye" metni Rol.KURYE'nin değeri. Burada Rol'ü içeri almıyoruz:
    # `hesaplar` zaten `core`'dan ZamanDamgali alıyor, ters yönde içe aktarma
    # döngü yaratır.
    kurye = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="kurye", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="rotalari",
        limit_choices_to={"rol": "kurye"},
        help_text="Boş bırakılırsa bu rotayı mağazanın bütün kuryeleri görür.")

    class Meta:
        verbose_name = "teslim takvimi"
        verbose_name_plural = "teslim takvimi"
        ordering = ["tarih", "hizmet_mahallesi"]
        unique_together = [("hizmet_mahallesi", "tarih")]

    def __str__(self):
        return f"{self.hizmet_mahallesi.mahalle.ad} — {self.tarih:%d.%m.%Y}"

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
    def kuryenin_rotalari(cls, kullanici, sorgu=None):
        """
        Bu kullanıcının görmesi gereken rotalar.

        Kurye: kendine atanmış rotalar **ve** hiç kimseye atanmamış olanlar.
        Atama boş bırakıldığında eski davranış sürüyor — tek kuryeyle çalışan
        mağaza hiçbir şey yapmak zorunda kalmıyor. İkinci kurye işe girince
        yönetici atamaya başlar, o andan sonra herkes yalnızca kendi rotasını
        görür.

        Yönetici ve süper admin: hepsi.
        """
        sorgu = cls.objects.all() if sorgu is None else sorgu
        if getattr(kullanici, "rol", None) != "kurye":
            return sorgu
        return sorgu.filter(models.Q(kurye=kullanici) | models.Q(kurye__isnull=True))

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
                hizmet_mahallesi=kural.hizmet_mahallesi,
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

    İki yerden besleniyor:

    1. Ana sayfadaki "yakında" formu — ziyaretçi, üyeliği yok, e-posta bırakır.
    2. Adres ekranı — **üye**, kargo göndermediğimiz bir ilçeyi seçmiş.
       Kayıt olmuş biri olduğu için e-postası olmayabilir (e-posta isteğe bağlı),
       ama `uye` ve `ilce` biliniyor.

    Bu yüzden `eposta` zorunlu değil; onun yerine *"hiç iletişim bilgisi yok"*
    durumu `clean()` ile engelleniyor. Zorunlu tutsaydık ikinci kaynak hiç
    kaydedilemezdi.
    """

    # "Mahalleme de gelin" sayfası isim de soruyor: haber verirken kimi aradığımızı
    # bilelim. Eski kayıtlarda (yakında formu, adres formu) boş kalır.
    ad_soyad = models.CharField("ad soyad", max_length=120, blank=True)
    eposta = models.EmailField("e-posta", blank=True)
    telefon = models.CharField("telefon", max_length=20, blank=True)
    uye = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name="üye",
                            on_delete=models.SET_NULL, null=True, blank=True,
                            related_name="ilgi_kayitlari",
                            help_text="Kayıt bir üyeden geldiyse. Ziyaretçide boş.")
    ilce = models.ForeignKey(Ilce, verbose_name="ilçe", on_delete=models.SET_NULL,
                             null=True, blank=True, related_name="ilgi_kayitlari",
                             help_text="Hangi ilçeye talep var. Listeyi buna göre süzüyoruz.")
    # Resmî mahalle biliniyorsa buraya bağlanıyor. Serbest metinle gruplamak
    # güvenilmez: "Müftü", "müftü mah.", "Müftü Mahallesi" üç ayrı satır olur
    # ve talep sayısı üçe bölünür — tam da güvenmek istediğimiz sayı.
    mahalle = models.ForeignKey(Mahalle, verbose_name="mahalle (resmî)",
                                on_delete=models.SET_NULL, null=True, blank=True,
                                related_name="ilgi_kayitlari",
                                help_text="Mahalle listede varsa seçilir; yoksa boş kalır.")
    mahalle_adi = models.CharField("mahalle (yazılan)", max_length=120, blank=True,
                                   help_text="Kişinin yazdığı mahalle adı. "
                                             "Resmî mahalle seçilemediğinde buraya bakılır.")
    kaynak = models.CharField("kaynak", max_length=60, blank=True,
                              help_text="Örnek: instagram, tanıdık, arama, adres formu")
    haber_verildi = models.BooleanField("haber verildi", default=False)

    class Meta:
        verbose_name = "ilgi kaydı"
        verbose_name_plural = "ilgi kayıtları"
        ordering = ["-olusturuldu"]

    def __str__(self):
        return self.kime_ulasilir or self.yer or "ilgi kaydı"

    @property
    def kime_ulasilir(self):
        """Elimizdeki iletişim yolu. Haber verme listesi bunu kullanacak."""
        if self.eposta:
            return self.eposta
        if self.telefon:
            return self.telefon
        if self.uye_id:
            return str(self.uye)
        return ""

    @property
    def yer(self):
        """'Yenişehir · Meram / Konya' — mahalle yazılmamışsa yalnızca ilçe."""
        mahalle = self.mahalle.ad if self.mahalle_id else self.mahalle_adi
        parcalar = [p for p in (mahalle, str(self.ilce) if self.ilce_id else "") if p]
        return " · ".join(parcalar)

    def save(self, *args, **kwargs):
        # Kişi mahalleyi serbest yazdıysa, resmî listede karşılığı varsa
        # bağlayalım: talep sayıları yazım farkları yüzünden bölünmesin.
        if self.mahalle_id is None and self.mahalle_adi and self.ilce_id:
            from .araclar import turkce_slug

            self.mahalle = self.ilce.mahalleler.filter(
                slug=turkce_slug(self.mahalle_adi)).first()
        super().save(*args, **kwargs)

    def clean(self):
        # Ulaşılamayacak kayıt listeyi kalabalıklaştırır, işe yaramaz.
        if not (self.eposta or self.telefon or self.uye_id):
            raise ValidationError(
                {"eposta": "E-posta, telefon ya da üye — en az biri gerekli."})


# ==========================================================================
# SATIŞ AYARLARI — panelden düzenlenir
# ==========================================================================
class SatisAyarlari(ZamanDamgali):
    """
    Mağazanın ticari eşikleri: minimum sepet, teslimat ücreti, ücretsiz
    teslimat eşiği, provizyon tamponu.

    **Neden veritabanında, ayar dosyasında değil?** Bunlar iş kararı ve sık
    değişir. Teslimat ücretini 45 ₺ yapmak için kod düzeltip yeniden yayın
    yapmak saçma; mağaza yöneticisi panelden değiştirmeli.

    **Neden mağaza başına?** Karaman'ın teslimat ücreti Beyşehir'den farklı
    olabilir; mahalle yoğunluğu ve mesafe farklı.

    `.env` değerleri artık yalnızca **ilk kurulum varsayılanı**: yeni bir
    mağaza açıldığında bu kayıt o değerlerle oluşturulur, sonrası panelde.
    """

    class VitrinModu(models.TextChoices):
        KAPALI = "kapali", "Kapalı — yalnızca yakında sayfası"
        TEST = "test", "Test — vitrin yalnızca giriş yapanlara açık"
        ACIK = "acik", "Açık — herkese satış"

    magaza = models.OneToOneField(Magaza, on_delete=models.CASCADE,
                                  related_name="satis_ayarlari", verbose_name="mağaza")

    vitrin_modu = models.CharField(
        "vitrin modu", max_length=10, choices=VitrinModu.choices, default=VitrinModu.TEST,
        help_text="Sanal POS ve yasal metinler tamamlanana kadar TEST'te kalmalı. "
                  "Test modunda verilen siparişler deneme sayılır ve raporlara girmez.")

    min_sepet_tutari = models.DecimalField(
        "minimum sepet tutarı (₺)", max_digits=10, decimal_places=2,
        validators=[MinValueValidator(Decimal("0"))],
        help_text="Bu tutarın altındaki sepetle sipariş verilemez. 0 yazarsanız sınır kalkar.")
    teslimat_ucreti = models.DecimalField(
        "teslimat ücreti (₺)", max_digits=10, decimal_places=2,
        validators=[MinValueValidator(Decimal("0"))],
        help_text="Her siparişe eklenir. 0 yazarsanız teslimat her zaman ücretsiz olur.")
    ucretsiz_teslimat_esigi = models.DecimalField(
        "ücretsiz teslimat eşiği (₺)", max_digits=10, decimal_places=2,
        null=True, blank=True, validators=[MinValueValidator(Decimal("0"))],
        help_text="Bu tutarın üstündeki siparişte teslimat ücreti alınmaz. "
                  "Boş bırakırsanız ücretsiz teslimat hiç olmaz.")
    provizyon_tampon_orani = models.DecimalField(
        "provizyon tamponu", max_digits=4, decimal_places=3,
        validators=[MinValueValidator(Decimal("0"))],
        help_text="Tartılı üründe karttan bloke edilecek fazlalık. "
                  "0,150 = %15. Tartı tahminden fazla çıkarsa bu pay işe yarar.")

    otomatik_teslim_onayi_saat = models.PositiveSmallIntegerField(
        "otomatik teslim onayı (saat)", default=24,
        help_text="Üye \"eksiksiz teslim aldım\" demezse kaç saat sonra onaylanmış sayılır.")
    talep_acma_suresi_saat = models.PositiveSmallIntegerField(
        "talep açma süresi (saat)", default=24,
        help_text="Teslimden sonra kaç saat içinde iade veya şikâyet açılabilir.")

    class Meta:
        verbose_name = "satış ayarları"
        verbose_name_plural = "satış ayarları"
        ordering = ["magaza__ad"]

    def __str__(self):
        return f"{self.magaza.ad} — satış ayarları"

    # -- kurulum -----------------------------------------------------------
    @staticmethod
    def varsayilanlar():
        """İlk kurulum değerleri `settings.BOSTANHANE`'den (yani .env'den) gelir."""
        kaynak = settings.BOSTANHANE
        return {
            "min_sepet_tutari": Decimal(str(kaynak["MIN_SEPET_TUTARI"])),
            "teslimat_ucreti": Decimal(str(kaynak["TESLIMAT_UCRETI"])),
            "ucretsiz_teslimat_esigi": Decimal(str(kaynak["UCRETSIZ_TESLIMAT_ESIGI"])),
            "provizyon_tampon_orani": Decimal(str(kaynak["PROVIZYON_TAMPON_ORANI"])),
            "otomatik_teslim_onayi_saat": int(kaynak["OTOMATIK_TESLIM_ONAYI_SAAT"]),
            "talep_acma_suresi_saat": int(kaynak["TALEP_ACMA_SURESI_SAAT"]),
        }

    @classmethod
    def getir(cls, magaza):
        """
        Mağazanın ayarlarını döner; yoksa varsayılanlarla oluşturur.
        Kodun her yerinden güvenle çağrılabilir — ayar kaydı yok diye hata vermez.
        """
        ayar, _ = cls.objects.get_or_create(magaza=magaza, defaults=cls.varsayilanlar())
        return ayar

    # -- hesaplar ----------------------------------------------------------
    def teslimat_ucreti_hesapla(self, ara_toplam):
        """Sepet ara toplamına göre teslimat ücreti. Eşik geçildiyse sıfır."""
        ara_toplam = Decimal(str(ara_toplam))
        if self.ucretsiz_teslimat_esigi is not None and ara_toplam >= self.ucretsiz_teslimat_esigi:
            return Decimal("0.00")
        return self.teslimat_ucreti

    def ucretsize_kalan(self, ara_toplam):
        """Ücretsiz teslimata ne kadar kaldı? Eşik yoksa veya geçildiyse None."""
        if self.ucretsiz_teslimat_esigi is None:
            return None
        kalan = self.ucretsiz_teslimat_esigi - Decimal(str(ara_toplam))
        return kalan if kalan > 0 else None

    def sepet_eksigi(self, ara_toplam):
        """Minimum sepete ne kadar eksik? Yeterliyse None."""
        eksik = self.min_sepet_tutari - Decimal(str(ara_toplam))
        return eksik if eksik > 0 else None

    def sepet_uygun_mu(self, ara_toplam):
        return self.sepet_eksigi(ara_toplam) is None

    def provizyon_tutari(self, tutar):
        """Tartılı sepet için karttan bloke edilecek tutar."""
        tutar = Decimal(str(tutar))
        return (tutar * (Decimal("1") + self.provizyon_tampon_orani)).quantize(Decimal("0.01"))

    # -- vitrin ------------------------------------------------------------
    @property
    def vitrin_acik_mi(self):
        """Herkese açık satış yapılıyor mu?"""
        return self.vitrin_modu == self.VitrinModu.ACIK

    @property
    def test_modunda_mi(self):
        return self.vitrin_modu == self.VitrinModu.TEST

    def vitrin_gorunur_mu(self, kullanici):
        """
        Bu ziyaretçi vitrini görebilir mi?

        kapali → kimse (yakında sayfası)
        test   → yalnızca giriş yapmış kişiler
        acik   → herkes
        """
        if self.vitrin_modu == self.VitrinModu.ACIK:
            return True
        if self.vitrin_modu == self.VitrinModu.KAPALI:
            return False
        return bool(getattr(kullanici, "is_authenticated", False))

    def clean(self):
        super().clean()
        if (self.ucretsiz_teslimat_esigi is not None
                and self.min_sepet_tutari is not None
                and self.ucretsiz_teslimat_esigi < self.min_sepet_tutari):
            raise ValidationError({
                "ucretsiz_teslimat_esigi":
                    "Ücretsiz teslimat eşiği, minimum sepet tutarından küçük. "
                    "Bu haliyle her sipariş ücretsiz teslimat alır — istediğiniz bu değilse "
                    "eşiği yükseltin, gerçekten buysa teslimat ücretini 0 yapmak daha anlaşılır."
            })


@receiver(post_save, sender=Magaza)
def magaza_satis_ayarlarini_ac(sender, instance, created, **kwargs):
    """Yeni mağaza açıldığında satış ayarları kaydı kendiliğinden oluşsun."""
    if created:
        SatisAyarlari.getir(instance)
