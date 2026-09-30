"""
Bostanhane — hesaplar uygulaması modelleri

Bu dosya `hesaplar/models.py` yerine geçer.

İki model var:
  Kullanici → sisteme giren herkes: süper admin, mağaza yöneticisi,
              paketleme elemanı, kurye ve üye. Hepsi tek tabloda,
              ayırt eden şey `rol` alanı.
  Adres     → üyenin teslimat adresi. Mahalleye bağlıdır, çünkü teslim
              günü mahalleden gelir.

Neden tek kullanıcı tablosu? Bir kişi zamanla rol değiştirebilir
(kurye, mağaza yöneticisi olabilir). Ayrı tablolarda tutsak o kişiyi
taşımak gerekirdi; tek tabloda `rol` alanını değiştirmek yetiyor.

Neden giriş telefonla? Müşteri kullanıcı adı uydurmak istemez, telefonunu
zaten biliyor. SMS doğrulaması da aynı numara üzerinden yürüyecek.

DİKKAT — İNGİLİZCE ALAN ADLARI:
Projede alan adları Türkçedir, ama Django'nun kimlik doğrulama sistemi
şu alan adlarını kendisi arar ve başka isim kabul etmez:
    password, last_login, is_active, is_staff, is_superuser
Bu beşini İngilizce bırakmak zorundayız; `verbose_name` değerlerini
Türkçe yazarak panelde düzgün görünmelerini sağlıyoruz.
"""

import re

from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.exceptions import ValidationError
from django.db import models, transaction

from core.models import ZamanDamgali


# --------------------------------------------------------------------------
# Telefon numarası yardımcıları
# --------------------------------------------------------------------------
def telefon_duzelt(deger):
    """
    Girilen telefonu tek biçime indirir: 10 hane, 5 ile başlar.

    Kullanıcı numarasını her türlü yazar. Hepsini aynı biçimde saklamazsak
    "bu numara kayıtlı mı" sorusunun cevabı yazım şekline göre değişir.

        '0532 111 22 33'    → '5321112233'
        '+90 532 111 22 33' → '5321112233'
        '905321112233'      → '5321112233'
    """
    if not deger:
        return ""
    rakamlar = re.sub(r"\D", "", str(deger))
    if len(rakamlar) == 12 and rakamlar.startswith("90"):
        rakamlar = rakamlar[2:]
    elif len(rakamlar) == 11 and rakamlar.startswith("0"):
        rakamlar = rakamlar[1:]
    return rakamlar


def telefon_dogrula(deger):
    """Türkiye cep numarası biçimini denetler. Hatalıysa anlaşılır Türkçe hata verir."""
    duzeltilmis = telefon_duzelt(deger)
    if len(duzeltilmis) != 10 or not duzeltilmis.startswith("5"):
        raise ValidationError(
            "Telefon numarası 10 haneli olmalı ve 5 ile başlamalı. Örnek: 5321112233"
        )


def telefon_okunur_yaz(deger):
    """'5321112233' → '0532 111 22 33'. Sadece ekranda göstermek için."""
    d = telefon_duzelt(deger)
    if len(d) != 10:
        return deger or ""
    return f"0{d[0:3]} {d[3:6]} {d[6:8]} {d[8:10]}"


# --------------------------------------------------------------------------
# Roller
# --------------------------------------------------------------------------
class Rol(models.TextChoices):
    SUPER_ADMIN = "super_admin", "Süper Admin"
    MAGAZA_YONETICISI = "magaza_yoneticisi", "Mağaza Yöneticisi"
    PAKETLEME = "paketleme", "Paketleme Elemanı"
    KURYE = "kurye", "Kurye"
    UYE = "uye", "Üye"


# Mağazaya bağlı çalışan roller. Bu rollerde mağaza alanı boş bırakılamaz.
MAGAZAYA_BAGLI_ROLLER = frozenset({
    Rol.MAGAZA_YONETICISI, Rol.PAKETLEME, Rol.KURYE,
})

# Django yönetim paneline (/yonetim/) girebilen roller.
# Paketleme ve kurye panele girmez; onların kendi sade ekranları olacak.
PANEL_ROLLERI = frozenset({
    Rol.SUPER_ADMIN, Rol.MAGAZA_YONETICISI,
})

# Müşteri olmayan, yani şirket içi roller.
PERSONEL_ROLLERI = frozenset({
    Rol.SUPER_ADMIN, Rol.MAGAZA_YONETICISI, Rol.PAKETLEME, Rol.KURYE,
})


# --------------------------------------------------------------------------
# Kullanıcı yöneticisi (kayıt oluşturan yardımcı)
# --------------------------------------------------------------------------
class KullaniciYoneticisi(BaseUserManager):
    """
    `Kullanici.objects` bu sınıftır. Django kullanıcı oluştururken
    buradaki iki yöntemi çağırır: create_user ve create_superuser.
    """

    use_in_migrations = True

    def _olustur(self, telefon, sifre, **ekstra):
        telefon_dogrula(telefon)
        kullanici = self.model(telefon=telefon_duzelt(telefon), **ekstra)
        if sifre:
            kullanici.set_password(sifre)
        else:
            # Şifresiz hesap: giriş yapamaz. Personeli önce oluşturup
            # şifresini sonra vermek istediğimizde işe yarar.
            kullanici.set_unusable_password()
        kullanici.save(using=self._db)
        return kullanici

    def create_user(self, telefon, password=None, **ekstra):
        ekstra.setdefault("rol", Rol.UYE)
        ekstra.setdefault("is_staff", False)
        ekstra.setdefault("is_superuser", False)
        return self._olustur(telefon, password, **ekstra)

    def create_superuser(self, telefon, password=None, **ekstra):
        ekstra["rol"] = Rol.SUPER_ADMIN
        ekstra["is_staff"] = True
        ekstra["is_superuser"] = True
        ekstra["is_active"] = True
        return self._olustur(telefon, password, **ekstra)


# --------------------------------------------------------------------------
# Kullanıcı
# --------------------------------------------------------------------------
class Kullanici(AbstractBaseUser, PermissionsMixin, ZamanDamgali):
    """Sisteme giren herkes. Rol alanı kimin ne yapabileceğini belirler."""

    telefon = models.CharField(
        "telefon", max_length=10, unique=True,
        validators=[telefon_dogrula],
        help_text="10 hane, başında sıfır olmadan. Örnek: 5321112233")
    ad_soyad = models.CharField("ad soyad", max_length=120)
    eposta = models.EmailField("e-posta", blank=True,
                               help_text="Zorunlu değil. Fatura ve bildirim için kullanılır.")

    rol = models.CharField("rol", max_length=20, choices=Rol.choices, default=Rol.UYE)
    magaza = models.ForeignKey(
        "core.Magaza", on_delete=models.PROTECT, null=True, blank=True,
        related_name="personel", verbose_name="bağlı mağaza",
        help_text="Mağaza yöneticisi, paketleme ve kurye için zorunlu. "
                  "Süper admin ve üyede boş kalır.")

    telefon_dogrulandi = models.BooleanField(
        "telefon doğrulandı", default=False,
        help_text="SMS ile doğrulandıysa işaretlidir.")
    kvkk_onayi = models.DateTimeField(
        "KVKK onay zamanı", null=True, blank=True,
        help_text="Üyelik sırasında aydınlatma metnini onayladığı an.")
    duyuru_izni = models.BooleanField(
        "kampanya bildirimi izni", default=False,
        help_text="Kapalıysa tanıtım mesajı gönderilmez. Sipariş bildirimleri bundan bağımsızdır.")

    # Django'nun beklediği İngilizce adlı iki alan (dosya başındaki nota bakın)
    is_active = models.BooleanField(
        "aktif", default=True,
        help_text="Kapalıysa bu kişi sisteme giriş yapamaz. Hesabı silmek yerine bunu kapatın.")
    is_staff = models.BooleanField(
        "yönetim paneline girebilir", default=False,
        help_text="Rol seçimine göre otomatik ayarlanır; elle değiştirmeniz gerekmez.")

    objects = KullaniciYoneticisi()

    USERNAME_FIELD = "telefon"       # giriş anahtarı
    REQUIRED_FIELDS = ["ad_soyad"]   # createsuperuser bunu da sorar
    EMAIL_FIELD = "eposta"

    class Meta:
        verbose_name = "kullanıcı"
        verbose_name_plural = "kullanıcılar"
        ordering = ["ad_soyad"]

    def __str__(self):
        return f"{self.ad_soyad} · {self.telefon_okunur}"

    # -- görünüm yardımcıları ---------------------------------------------
    @property
    def telefon_okunur(self):
        return telefon_okunur_yaz(self.telefon)

    def get_full_name(self):
        return self.ad_soyad

    def get_short_name(self):
        return self.ad_soyad.split(" ")[0] if self.ad_soyad else self.telefon

    # -- rol soruları ------------------------------------------------------
    @property
    def super_admin_mi(self):
        return self.rol == Rol.SUPER_ADMIN or self.is_superuser

    @property
    def magaza_yoneticisi_mi(self):
        return self.rol == Rol.MAGAZA_YONETICISI

    @property
    def paketleme_mi(self):
        return self.rol == Rol.PAKETLEME

    @property
    def kurye_mi(self):
        return self.rol == Rol.KURYE

    @property
    def uye_mi(self):
        return self.rol == Rol.UYE

    @property
    def personel_mi(self):
        return self.rol in PERSONEL_ROLLERI

    @property
    def tum_magazalari_gorur(self):
        """Süper admin bütün mağazaları görür; diğer herkes yalnızca kendisininkini."""
        return self.super_admin_mi

    def gorebilecegi_magaza(self):
        """
        Sorgu filtrelerinde kullanılır.
        None dönerse "kısıtlama yok" demektir (süper admin).
        """
        return None if self.tum_magazalari_gorur else self.magaza

    @property
    def varsayilan_adres(self):
        return self.adresler.filter(aktif=True, varsayilan=True).first()

    # -- doğrulama ve kayıt ------------------------------------------------
    def clean(self):
        super().clean()
        self.telefon = telefon_duzelt(self.telefon)
        if self.rol in MAGAZAYA_BAGLI_ROLLER and self.magaza_id is None:
            raise ValidationError({
                "magaza": f"{self.get_rol_display()} rolü için mağaza seçilmelidir."
            })
        if self.rol == Rol.UYE and self.magaza_id is not None:
            raise ValidationError({
                "magaza": "Üyeler mağazaya bağlanmaz; üyenin mağazası adresinden belirlenir."
            })

    def save(self, *args, **kwargs):
        self.telefon = telefon_duzelt(self.telefon)
        # Panele giriş hakkı role göre belirlenir; elle karıştırılmasın.
        if self.rol in PANEL_ROLLERI:
            self.is_staff = True
        elif self.rol == Rol.UYE:
            self.is_staff = False
            self.is_superuser = False
        super().save(*args, **kwargs)
        self.rol_grubunu_uygula()

    def rol_grubunu_uygula(self):
        """
        Rolün yetki grubunu bağlar, diğer rol gruplarını çıkarır.

        Böylece bir kurye mağaza yöneticisi yapıldığında yetkileri de birlikte
        değişir; kimse elle kutucuk işaretlemek zorunda kalmaz.

        Gruplar `python manage.py roller_kur` komutuyla oluşturulur. Henüz
        oluşturulmadıysa burada bir şey yapılmaz — kurulumun ilk anında
        (migrate sırasında) hata vermemesi için.
        """
        from django.contrib.auth.models import Group
        from django.db import DatabaseError

        from .izinler import ROL_GRUP_ADLARI

        hedef_ad = ROL_GRUP_ADLARI.get(self.rol)
        try:
            for grup in Group.objects.filter(name__in=ROL_GRUP_ADLARI.values()):
                if grup.name == hedef_ad:
                    self.groups.add(grup)
                else:
                    self.groups.remove(grup)
        except DatabaseError:
            pass


# --------------------------------------------------------------------------
# Adres
# --------------------------------------------------------------------------
class Adres(ZamanDamgali):
    """
    Üyenin teslimat adresi.

    Resmî (coğrafi) mahalleye bağlanır — Türkiye'nin her yerinde adres girilebilir,
    çünkü kargo kanalı her yere gidiyor. Yerel teslimatın açık olup olmadığı
    `yerel_teslimat_var` ile anlaşılır: o mahalleye giden bir mağaza varsa açık.

    Serbest metin adres yazdırsak "bu adres hangi gün gidiyor" sorusunu
    cevaplayamazdık; teslim günü mahalleden gelir.
    """

    uye = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                            related_name="adresler", verbose_name="üye")
    baslik = models.CharField("adres başlığı", max_length=40, default="Ev",
                             help_text="Örnek: Ev, İş, Annem")

    mahalle = models.ForeignKey("core.Mahalle", on_delete=models.PROTECT,
                               related_name="adresler", verbose_name="mahalle")
    acik_adres = models.TextField("açık adres",
                                  help_text="Cadde, sokak, apartman adı.")
    bina_no = models.CharField("bina no", max_length=10, blank=True)
    kat = models.CharField("kat", max_length=10, blank=True)
    daire = models.CharField("daire", max_length=10, blank=True)

    # Teslimatı başka biri alacaksa
    teslim_alacak = models.CharField("teslim alacak kişi", max_length=120, blank=True,
                                     help_text="Boşsa üyenin kendi adı kullanılır.")
    teslim_telefonu = models.CharField("teslimat telefonu", max_length=10, blank=True,
                                       help_text="Boşsa üyenin telefonu kullanılır.")
    tarif = models.CharField("kuryeye not", max_length=200, blank=True,
                             help_text="Örnek: Zil çalışmıyor, arayın. Bakkalın üstü.")

    # Haritadan seçilen iğne. Kurye rotası bunu kullanacak.
    enlem = models.DecimalField("enlem", max_digits=9, decimal_places=6, null=True, blank=True)
    boylam = models.DecimalField("boylam", max_digits=9, decimal_places=6, null=True, blank=True)

    varsayilan = models.BooleanField("varsayılan adres", default=False,
                                     help_text="Sepette önce bu adres seçili gelir.")
    aktif = models.BooleanField("aktif", default=True,
                                help_text="Silmek yerine kapatılır; eski siparişlerin adresi bozulmasın.")

    class Meta:
        verbose_name = "adres"
        verbose_name_plural = "adresler"
        ordering = ["-varsayilan", "baslik"]
        unique_together = [("uye", "baslik")]

    def __str__(self):
        return f"{self.baslik} — {self.mahalle.ad}"

    @property
    def hizmet_mahallesi(self):
        """Bu adrese giden mağazanın hizmet kaydı. None ise yerel teslimat yok."""
        return self.mahalle.yerel_hizmet()

    @property
    def magaza(self):
        """Adresin hangi mağazaya düştüğü mahalleden gelir. Kargo bölgesinde None."""
        hizmet = self.hizmet_mahallesi
        return hizmet.magaza if hizmet else None

    @property
    def yerel_teslimat_var(self):
        """Mahalleye giden bir mağaza var mı? Yoksa yalnızca kargo seçeneği çıkar."""
        return self.hizmet_mahallesi is not None

    @property
    def kime(self):
        return self.teslim_alacak or self.uye.ad_soyad

    @property
    def hangi_telefon(self):
        return self.teslim_telefonu or self.uye.telefon

    def tam_adres(self):
        """Etiket ve kurye ekranı için tek satırlık okunur adres."""
        parcalar = [self.acik_adres.strip()]
        if self.bina_no:
            parcalar.append(f"No: {self.bina_no}")
        if self.kat:
            parcalar.append(f"Kat: {self.kat}")
        if self.daire:
            parcalar.append(f"Daire: {self.daire}")
        parcalar.append(self.mahalle.tam_ad)
        return " · ".join(p for p in parcalar if p)

    tam_adres.short_description = "adres"

    def clean(self):
        super().clean()
        if self.teslim_telefonu:
            self.teslim_telefonu = telefon_duzelt(self.teslim_telefonu)
            telefon_dogrula(self.teslim_telefonu)

    def save(self, *args, **kwargs):
        if self.teslim_telefonu:
            self.teslim_telefonu = telefon_duzelt(self.teslim_telefonu)

        with transaction.atomic():
            kardesler = Adres.objects.filter(uye=self.uye_id)
            if self.pk:
                kardesler = kardesler.exclude(pk=self.pk)
            # İlk adres otomatik varsayılan olur; kullanıcı ayrıca uğraşmasın.
            if not kardesler.exists():
                self.varsayilan = True

            super().save(*args, **kwargs)

            # Varsayılan tek olmalı. Kaydettikten sonra kendi numaramız belli
            # olduğu için sorguyu burada yeniden kuruyoruz; aksi halde bu kayıt
            # kendi varsayılanlığını kapatırdı.
            if self.varsayilan:
                Adres.objects.filter(uye=self.uye_id, varsayilan=True) \
                             .exclude(pk=self.pk).update(varsayilan=False)
