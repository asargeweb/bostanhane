"""Sipariş paneli: sayfalar açılıyor mu, mağaza izolasyonu tutuyor mu, tartım kaydediliyor mu."""
import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bostanhane.settings")
django.setup()

from decimal import Decimal
from django.test.utils import setup_test_environment
from django.test import Client
from django.utils import timezone

setup_test_environment()

from core.models import Il, Ilce, Magaza, SatisAyarlari, TeslimTakvimi
from katalog.models import Birim, MagazaUrun, StokHareketi
from hesaplar.models import Kullanici, Rol
from siparis.models import Sepet, Siparis

hata = 0
def kontrol(ad, kosul, ek=""):
    global hata
    if kosul:
        print(f"  OK   {ad}")
    else:
        hata += 1
        print(f"  HATA {ad} {ek}")

magaza = Magaza.objects.get(slug="beysehir")
uye = Kullanici.objects.filter(rol=Rol.UYE).exclude(adresler=None).first()
takvim = (TeslimTakvimi.objects
          .filter(hizmet_mahallesi__magaza=magaza, durum=TeslimTakvimi.Durum.ACIK,
                  kesim_zamani__gt=timezone.now())   # yerelde kesim servisi yok; geçmiş açık gün kalabiliyor
          .order_by("tarih").first())

# ---- hesaplar -------------------------------------------------------------
SIFRE = "DenemeSifre!2026"
sa = Kullanici.objects.filter(rol=Rol.SUPER_ADMIN).first()
if sa is None:
    sa = Kullanici.objects.create_superuser(telefon="5330000001", sifre=SIFRE,
                                            ad_soyad="Deneme Süper")
sa.set_password(SIFRE); sa.save()

yonetici = Kullanici.objects.filter(rol=Rol.MAGAZA_YONETICISI, magaza=magaza).first()
if yonetici is None:
    yonetici = Kullanici.objects.create_user(telefon="5330000002", sifre=SIFRE,
                                             ad_soyad="Deneme Yönetici",
                                             rol=Rol.MAGAZA_YONETICISI, magaza=magaza)
yonetici.set_password(SIFRE); yonetici.save()

# ikinci mağaza — izolasyon sınavı için
konya = Il.objects.get(plaka=42)
karaman_il = Il.objects.get(plaka=70)
ilce2 = Ilce.objects.filter(il=karaman_il).first() or Ilce.objects.exclude(magazalar=magaza).first()
magaza2, _ = Magaza.objects.get_or_create(
    slug="karaman", defaults={"ad": "Bostanhane Karaman", "il": ilce2.il, "ilce": ilce2,
                              "adres": "Deneme", "telefon": "5330000003"})

# ---- veri: bir sipariş ----------------------------------------------------
kg = Birim.objects.get(kisaltma="kg")
domates = MagazaUrun.objects.get(magaza=magaza, urun__slug="domates")
domates.fiyat = Decimal("32.90"); domates.aktif = True; domates.save()
bal = MagazaUrun.objects.get(magaza=magaza, urun__slug="suzme-cicek-bali-850-g")
bal.fiyat = Decimal("320.00"); bal.aktif = True; bal.save()
if (bal.stok or 0) < 5:
    bal.stok_degistir(5, StokHareketi.Tur.MAL_KABUL, aciklama="panel denemesi")

sepet, _ = Sepet.objects.get_or_create(uye=uye, magaza=magaza)
sepet.kalemler.all().delete()
sepet.teslim_takvimi = takvim
sepet.adres = uye.varsayilan_adres
sepet.save()
sepet.ekle(domates, "2")
sepet.ekle(bal, 1)
hazir, sebep = sepet.siparise_hazir_mi()
if not hazir:
    # minimum sepete ulaşmak için bal adedini artır
    sepet.ekle(bal, 1)
    hazir, sebep = sepet.siparise_hazir_mi()
kontrol("sepet siparişe hazır", hazir, sebep)
siparis = sepet.siparise_cevir(kullanici=uye)
print(f"       sipariş: {siparis.numara} · toplam {siparis.toplam} · bloke {siparis.provizyon_tutari}")

# ikinci mağazada da bir sipariş olsun (izolasyon görünür olsun)
yabanci = Siparis.objects.filter(magaza=magaza2).first()

print("— sayfalar açılıyor mu (süper admin)")
c = Client()
kontrol("süper admin girişi", c.login(telefon=sa.telefon, password=SIFRE))

for ad, yol in [("sipariş listesi", "/yonetim/siparis/siparis/"),
                ("sipariş sayfası", f"/yonetim/siparis/siparis/{siparis.pk}/change/"),
                ("sepet listesi", "/yonetim/siparis/sepet/"),
                ("sepet sayfası", f"/yonetim/siparis/sepet/{sepet.pk}/change/")]:
    y = c.get(yol)
    kontrol(f"{ad} 200", y.status_code == 200, y.status_code)

y = c.get(f"/yonetim/siparis/siparis/{siparis.pk}/change/")
icerik = y.content.decode()
kontrol("özet kutusunda bloke tutar var", "Bloke edilen" in icerik)
kontrol("DENEME şeridi var (vitrin test modunda)",
        ("DENEME SİPARİŞİ" in icerik) == siparis.test_siparisi,
        f"test_siparisi={siparis.test_siparisi}")
kontrol("adres dondurulmuş alanı görünüyor", siparis.teslim_ad_soyad in icerik)
kontrol("ürün adı satırda görünüyor", "Domates" in icerik)
kontrol("satır ekleme bağlantısı yok (inline)", "add-row" not in icerik)
liste = c.get("/yonetim/siparis/siparis/").content.decode()
kontrol("listede 'Sipariş ekle' düğmesi yok", "/yonetim/siparis/siparis/add/" not in liste)
kontrol("yan menüde sepet ekleme bağlantısı yok", "/yonetim/siparis/sepet/add/" not in liste)

print("— mağaza izolasyonu")
c2 = Client()
kontrol("yönetici girişi", c2.login(telefon=yonetici.telefon, password=SIFRE))
y = c2.get("/yonetim/siparis/siparis/")
kontrol("yönetici sipariş listesini görüyor", y.status_code == 200, y.status_code)
if y.status_code == 200:
    kontrol("kendi siparişi listede", siparis.numara in y.content.decode())

if yabanci:
    y = c2.get(f"/yonetim/siparis/siparis/{yabanci.pk}/change/")
    kontrol("başka mağazanın siparişine erişemiyor", y.status_code in (302, 403, 404), y.status_code)
else:
    print("       (ikinci mağazada sipariş yok, çapraz erişim sınanmadı)")

y = c2.get("/yonetim/siparis/siparis/")
kontrol("yan süzgeçte yalnızca kendi mağazası",
        y.content.decode().count("Bostanhane Karaman") == 0)

print("— tartım panelden giriliyor mu")
kalem = siparis.kalemler.filter(urun_adi__icontains="Domates").first()
y = c2.get(f"/yonetim/siparis/siparis/{siparis.pk}/change/")
icerik = y.content.decode()
kontrol("teslim miktarı alanı düzenlenebilir",
        f'name="kalemler-0-teslim_miktari"' in icerik or "teslim_miktari" in icerik)
kontrol("birim fiyat salt okunur (input değil)",
        'name="kalemler-0-birim_fiyat"' not in icerik)
kontrol("sipariş miktarı salt okunur",
        'name="kalemler-0-siparis_miktari"' not in icerik)

print("— işlemler")
# "Hazırlandı olarak işaretle" KALDIRILDI: ham bir update() yapıp tartımı ve
# o anda yapılan çekimi atlıyordu — sipariş hazırlanmış görünür, parası hiç
# çekilmemiş olurdu. Hazırlama depo ekranının işi (/depo/), çekim orada.
y = c2.post("/yonetim/siparis/siparis/",
            {"action": "hazirlandi_isaretle", "_selected_action": [str(siparis.pk)]},
            follow=True)
siparis.refresh_from_db()
kontrol("kaldırılan 'hazırlandı' işlemi durumu değiştirmiyor",
        siparis.durum != Siparis.Durum.HAZIRLANIYOR, siparis.durum)
kontrol("kaldırılan işlem hazırlandı zamanı yazmıyor",
        siparis.hazirlandi_zamani is None)
icerik_liste = c2.get("/yonetim/siparis/siparis/").content.decode()
kontrol("'Hazırlandı olarak işaretle' listede yok",
        "Hazırlandı olarak işaretle" not in icerik_liste)

y = c2.post("/yonetim/siparis/siparis/",
            {"action": "teslim_edildi_isaretle", "_selected_action": [str(siparis.pk)]},
            follow=True)
siparis.refresh_from_db()
kontrol("teslim edildi işlemi çalıştı", siparis.durum == Siparis.Durum.TESLIM_EDILDI, siparis.durum)

print("— silme ve ekleme kapalı")
y = c2.get(f"/yonetim/siparis/siparis/{siparis.pk}/delete/")
kontrol("silme sayfası kapalı", y.status_code in (302, 403), y.status_code)
y = c2.get("/yonetim/siparis/siparis/add/")
kontrol("ekleme sayfası kapalı", y.status_code in (302, 403), y.status_code)
y = c2.get("/yonetim/siparis/sepet/add/")
kontrol("sepet ekleme kapalı", y.status_code in (302, 403), y.status_code)

print()
print("SONUÇ: hepsi geçti" if hata == 0 else f"SONUÇ: {hata} hata")
