"""Bildirim: SMS parça ölçümü, çift gönderim, hata yutma, deneme öneki, kilit, panel."""
import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bostanhane.settings")
django.setup()

import importlib
from datetime import datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace

from django.core.exceptions import ImproperlyConfigured
from django.test import override_settings
from django.test.utils import setup_test_environment
from django.utils import timezone
setup_test_environment()
from django.test import Client

from core.models import Magaza, SatisAyarlari, TeslimTakvimi
from katalog.models import MagazaUrun, StokHareketi
from hesaplar.models import Kullanici, Rol
from siparis.models import Sepet, Siparis
from odeme.islemler import provizyon_al
from bildirim import islemler, metinler
from bildirim.models import Bildirim, sms_parca_sayisi
from bildirim.saglayicilar import DenemeSmsSaglayici, sms_saglayici_sec

hata = 0
def kontrol(ad, kosul, ek=""):
    global hata
    print(f"  {'OK  ' if kosul else 'HATA'} {ad} {'' if kosul else ek}")
    if not kosul: hata += 1

SIFRE = "DenemeSifre!2026"
m = Magaza.objects.get(slug="beysehir")
ayarlar = SatisAyarlari.getir(m)
uye = Kullanici.objects.filter(rol=Rol.UYE).exclude(adresler=None).first()
takvim = TeslimTakvimi.objects.filter(hizmet_mahallesi__magaza=m).order_by("-tarih").first()
dom = MagazaUrun.objects.get(magaza=m, urun__slug="domates")
dom.fiyat = Decimal("32.90"); dom.aktif = True; dom.save()
bal = MagazaUrun.objects.get(magaza=m, urun__slug="suzme-cicek-bali-850-g")
bal.fiyat = Decimal("320.00"); bal.aktif = True; bal.save()
if (bal.stok or 0) < 10:
    bal.stok_degistir(10 - (bal.stok or 0), StokHareketi.Tur.MAL_KABUL, aciklama="bildirim")

def siparis_ac():
    takvim.durum = TeslimTakvimi.Durum.ACIK
    takvim.save(update_fields=["durum", "guncellendi"])
    s, _ = Sepet.objects.get_or_create(uye=uye, magaza=m); s.kalemler.all().delete()
    s.teslim_takvimi = takvim; s.adres = uye.varsayilan_adres; s.save()
    s.ekle(dom, "1.5"); s.ekle(bal, 2)
    return s.siparise_cevir(kullanici=uye)

# ==========================================================================
print("— SMS parça ölçümü: her metin tek parçaya sığmalı")
mah = SimpleNamespace(ad="Hacıarmağan")     # uzun mahalle adı, en kötü durum
tk = SimpleNamespace(hizmet_mahallesi=SimpleNamespace(mahalle=mah),
                     tarih=datetime(2026, 12, 24), kesim_zamani=datetime(2026, 12, 23, 18, 30))
kalem = SimpleNamespace(urun_adi="Süzme çiçek balı", birim_fiyat=Decimal("320.00"),
                        siparis_miktari=Decimal("2"))
ornek = SimpleNamespace(numara="BH-2026-000999", teslim_takvimi=tk,
                        teslim_ad_soyad="Ayşe Yılmaz", teslim_telefon="5334445566",
                        teslim_acik_adres="Atatürk Cd.", toplam=Decimal("1234.56"),
                        provizyon_tutari=Decimal("1456.78"), cekilen_tutar=Decimal("1198.70"))
ornek_talep = SimpleNamespace(siparis=ornek, iade_tutari=Decimal("1234.56"), karar_notu="…")

for imza in ("Bostanhane", ""):
    with override_settings(SMS_IMZA=imza):
        importlib.reload(metinler)
        sinavlar = {
            "sipariş alındı": metinler.siparis_alindi(ornek),
            "kesim yaklaştı": metinler.kesim_yaklasti(ornek, 120),
            "gün kesildi": metinler.gun_kesildi(ornek),
            "ürün bulunamadı": metinler.urun_bulunamadi(ornek, [kalem]),
            "yola çıktı": metinler.yola_cikti(ornek),
            "teslim edildi": metinler.teslim_edildi(ornek),
            "sipariş iptal": metinler.siparis_iptal(ornek),
            "talep kararı": metinler.talep_karari(ornek, ornek_talep),
        }
        etiket = "imzalı" if imza else "imzasız"
        for ad, (konu, sms, eposta) in sinavlar.items():
            adet, _ = sms_parca_sayisi(sms)
            kontrol(f"{ad} ({etiket}) tek parça", adet == 1, f"{len(sms)} kr, {adet} parça")
            kontrol(f"{ad} ({etiket}) e-posta dolu", len(eposta) > 50)
importlib.reload(metinler)
importlib.reload(islemler)

print("— parça hesabı doğru mu")
kontrol("GSM-7 160 karakter tek parça", sms_parca_sayisi("a" * 160) == (1, "GSM-7"))
kontrol("GSM-7 161 karakter iki parça", sms_parca_sayisi("a" * 161)[0] == 2)
kontrol("tek 'ş' sınırı 70'e düşürüyor", sms_parca_sayisi("ş" + "a" * 70)[0] == 2)
kontrol("70 Türkçe karakter tek parça", sms_parca_sayisi("ş" * 70)[0] == 1)
kontrol("ç ö ü GSM-7'de (sınır 160)", sms_parca_sayisi("çöü" + "a" * 100)[0] == 1)

# ==========================================================================
print("— sipariş alındı bildirimi")
Bildirim.objects.all().delete()
sip = siparis_ac()
provizyon_al(sip, kullanici=uye)
sip.refresh_from_db()
gonderilen = islemler.siparis_alindi_bildir(sip)
kontrol("bildirim üretildi", len(gonderilen) >= 1, len(gonderilen))
sms = Bildirim.objects.filter(siparis=sip, kanal=Bildirim.Kanal.SMS).first()
kontrol("SMS kaydı var", sms is not None)
if sms:
    kontrol("gönderildi", sms.gonderildi_mi, sms.hata_mesaji)
    kontrol("doğru numaraya", sms.adres == sip.teslim_telefon, sms.adres)
    kontrol("sağlayıcı deneme", sms.saglayici == "deneme")
    kontrol("mesaj numarası geldi", sms.saglayici_mesaj_no.startswith("DENEME-SMS"))
    kontrol("gönderim zamanı yazıldı", sms.gonderim_zamani is not None)
    # Deneme siparişinde "[DENEME] " öneki 9 karakter ekliyor; gerçek satışta
    # önek olmayacağı için asıl ölçüm öneksiz metin üzerinden.
    oneksiz = sms.metin.replace("[DENEME] ", "")
    kontrol("öneksiz hâli tek parça", sms_parca_sayisi(oneksiz)[0] == 1,
            f"{len(oneksiz)} kr, {sms_parca_sayisi(oneksiz)[0]} parça")

print("— deneme siparişinde [DENEME] öneki")
kontrol("sipariş deneme mi", sip.test_siparisi)
if sms:
    kontrol("metin [DENEME] ile başlıyor", sms.metin.startswith("[DENEME]"), sms.metin[:30])

print("— çift gönderim koruması")
onceki = Bildirim.objects.count()
islemler.siparis_alindi_bildir(sip)
islemler.siparis_alindi_bildir(sip)
kontrol("ikinci ve üçüncü çağrı yeni kayıt açmadı",
        Bildirim.objects.count() == onceki, Bildirim.objects.count() - onceki)

print("— hata yutma: bildirim siparişi bozmamalı")
sip2 = siparis_ac()
with override_settings(DENEME_BILDIRIM_HATASI="Sağlayıcı çöktü"):
    cikti = islemler.siparis_alindi_bildir(sip2)      # istisna fırlatmamalı
kontrol("istisna fırlatmadı", True)
bsz = Bildirim.objects.filter(siparis=sip2, durum=Bildirim.Durum.BASARISIZ)
kontrol("başarısız kayıt defterde", bsz.exists())
if bsz.exists():
    kontrol("hata mesajı yazıldı", bsz.first().hata_mesaji == "Sağlayıcı çöktü",
            bsz.first().hata_mesaji)
sip2.refresh_from_db()
kontrol("sipariş etkilenmedi", sip2.durum == Siparis.Durum.ALINDI, sip2.durum)

print("— metin üreticisi patlarsa da sipariş bozulmamalı")
eski = islemler.METIN_URETICILERI[Bildirim.Tur.YOLA_CIKTI]
def patlat(*a, **k):
    raise RuntimeError("metin hatası")
islemler.METIN_URETICILERI[Bildirim.Tur.YOLA_CIKTI] = patlat
sonuc = islemler.yola_cikti_bildir(sip)
kontrol("patlayan metinde boş liste döndü", sonuc == [])
islemler.METIN_URETICILERI[Bildirim.Tur.YOLA_CIKTI] = eski

print("— bulunamayan ürünler tek mesajda toplanıyor")
sip3 = siparis_ac()
for k in sip3.kalemler.all():
    k.tartim_gir(0, kullanici=uye)         # hepsi bulunamadı
sip3.refresh_from_db()
Bildirim.objects.filter(siparis=sip3).delete()
cikti = islemler.urun_bulunamadi_bildir(sip3)
smsler = Bildirim.objects.filter(siparis=sip3, kanal=Bildirim.Kanal.SMS)
kontrol("üç ürün için tek SMS", smsler.count() == 1, smsler.count())
if smsler.exists():
    kontrol("mesajda ürünler birlikte", smsler.first().metin.count(",") >= 1,
            smsler.first().metin)

print("— vitrin açıkken deneme göndericisi kilitli")
eski_mod = ayarlar.vitrin_modu
ayarlar.vitrin_modu = SatisAyarlari.VitrinModu.ACIK
ayarlar.save(update_fields=["vitrin_modu", "guncellendi"])
try:
    sms_saglayici_sec(m)
    kontrol("vitrin açıkken reddedilmeli", False)
except ImproperlyConfigured as e:
    kontrol("vitrin açıkken reddedildi", "deneme" in str(e))
print("— başlık (gönderen adı)")
# Sözleşme asarge adına, hesapta iki başlık olacak: BOSTANHANE / SECMENNEDIYOR.
# Başlık yazılmazsa firma kendi varsayılanını kullanır ve Bostanhane müşterisine
# öteki markanın adıyla mesaj gider. Vitrin gerçek satışa açılırken buna izin yok.
class GercekGibi(DenemeSmsSaglayici):
    ad = "gercek_gibi"
    gercek_gonderim = True

from bildirim import saglayicilar as _sag
_sag.SAGLAYICILAR[GercekGibi.ad] = GercekGibi
with override_settings(SMS_SAGLAYICI=GercekGibi.ad, SMS_BASLIK=""):
    try:
        sms_saglayici_sec(m)
        kontrol("vitrin açık + başlık boş reddedilmeli", False)
    except ImproperlyConfigured as e:
        kontrol("vitrin açık + başlık boş reddedildi", "SMS_BASLIK" in str(e))
with override_settings(SMS_SAGLAYICI=GercekGibi.ad, SMS_BASLIK="BOSTANHANE"):
    s = sms_saglayici_sec(m)
    kontrol("başlık doluyken geçiyor", s.baslik == "BOSTANHANE", s.baslik)
with override_settings(SMS_BASLIK=""):
    kontrol("başlık boşken sağlayıcıda da boş", sms_saglayici_sec().baslik == "")

print("— ayar hatası defterde takılı kayıt bırakmıyor")
# Vitrin açık + sağlayıcı "deneme" → seçim hata veriyor. Eskiden satır önce
# açıldığı için defterde "bekliyor" durumunda takılı bir kayıt kalıyordu ve
# istek anahtarı tutulduğu için ayar düzeltilse bile o mesaj bir daha
# denenmiyordu. (Bu hatayı CC buldu.)
sipX = siparis_ac()
Bildirim.objects.filter(siparis=sipX).delete()
cikti = islemler.siparis_alindi_bildir(sipX)          # vitrin hâlâ ACIK
kontrol("ayar hatasında bildirim dönmedi", cikti == [], cikti)
kontrol("defterde takılı kayıt yok",
        not Bildirim.objects.filter(siparis=sipX, kanal=Bildirim.Kanal.SMS).exists(),
        list(Bildirim.objects.filter(siparis=sipX).values_list("durum", flat=True)))

ayarlar.vitrin_modu = eski_mod
ayarlar.save(update_fields=["vitrin_modu", "guncellendi"])
kontrol("test modunda çalışıyor", sms_saglayici_sec(m).ad == "deneme")

# Ayar düzeldi: aynı mesaj şimdi gidebilmeli — anahtar serbest kalmış olmalı.
cikti = islemler.siparis_alindi_bildir(sipX)
smsX = Bildirim.objects.filter(siparis=sipX, kanal=Bildirim.Kanal.SMS).first()
kontrol("ayar düzelince mesaj gidiyor", smsX is not None and smsX.gonderildi_mi,
        smsX.durum if smsX else "kayıt yok")

# Metinlerin imzasız hâli yukarıda, "SMS parça ölçümü" bölümünde zaten ölçülüyor:
# başlık tahsis edilip imza kendiliğinden kalktığı gün hepsi tek parça kalıyor.

print("— kesim hatırlatma komutu")
from io import StringIO
from django.core.management import call_command
takvim.durum = TeslimTakvimi.Durum.ACIK
takvim.kesim_zamani = timezone.now() + timedelta(minutes=45)
takvim.save(update_fields=["durum", "kesim_zamani", "guncellendi"])
Bildirim.objects.filter(tur=Bildirim.Tur.KESIM_YAKLASTI).delete()
cikti = StringIO(); call_command("kesim_hatirlat", "--kuru", stdout=cikti)
metin = cikti.getvalue()
kontrol("kuru çalışma gönderim yapmadı",
        not Bildirim.objects.filter(tur=Bildirim.Tur.KESIM_YAKLASTI).exists())
kontrol("kuru çıktıda sipariş var", "BH-2026-" in metin, metin[-200:])
cikti = StringIO(); call_command("kesim_hatirlat", stdout=cikti)
gonderilen = Bildirim.objects.filter(tur=Bildirim.Tur.KESIM_YAKLASTI,
                                     kanal=Bildirim.Kanal.SMS)
kontrol("hatırlatma gönderildi", gonderilen.exists())
adet = gonderilen.count()
cikti2 = StringIO(); call_command("kesim_hatirlat", stdout=cikti2)
kontrol("ikinci çalıştırma yeni mesaj göndermedi",
        gonderilen.count() == adet, gonderilen.count() - adet)
kontrol("ikinci çıktıda 'zaten gönderilmiş'", "zaten gönderilmiş" in cikti2.getvalue())

print("— pencere dışındaki gün hatırlatılmıyor")
takvim.kesim_zamani = timezone.now() + timedelta(hours=10)
takvim.save(update_fields=["kesim_zamani", "guncellendi"])
Bildirim.objects.filter(tur=Bildirim.Tur.KESIM_YAKLASTI).delete()
cikti = StringIO(); call_command("kesim_hatirlat", stdout=cikti)
kontrol("10 saat sonrası hatırlatılmadı",
        not Bildirim.objects.filter(tur=Bildirim.Tur.KESIM_YAKLASTI).exists())
kontrol("çıktı 'hatırlatılacak gün yok'", "Hatırlatılacak gün yok" in cikti.getvalue())

print("— panel")
sa = Kullanici.objects.filter(rol=Rol.SUPER_ADMIN).first()
sa.set_password(SIFRE); sa.save()
c = Client(); c.login(telefon=sa.telefon, password=SIFRE)
y = c.get("/yonetim/bildirim/bildirim/")
kontrol("bildirim listesi 200", y.status_code == 200, y.status_code)
bir = Bildirim.objects.first()
y = c.get(f"/yonetim/bildirim/bildirim/{bir.pk}/change/")
kontrol("bildirim sayfası 200", y.status_code == 200, y.status_code)
kontrol("kaydet düğmesi yok", 'name="_save"' not in y.content.decode())
kontrol("ölçüm görünüyor", "karakter" in y.content.decode())
y = c.get("/yonetim/bildirim/bildirim/add/")
kontrol("ekleme kapalı", y.status_code in (302, 403), y.status_code)

# Mağaza yöneticisi de defteri görebilmeli: izinler.py'ye satır eklenmeyince
# bu adres 403 veriyor (siparis, odeme ve talep'te üç kez başımıza geldi).
my = Kullanici.objects.filter(rol=Rol.MAGAZA_YONETICISI, magaza=m).first()
my.set_password(SIFRE); my.save()
cy = Client(); cy.login(telefon=my.telefon, password=SIFRE)
y = cy.get("/yonetim/bildirim/bildirim/")
kontrol("mağaza yöneticisi listeyi görüyor (403 değil)", y.status_code == 200, y.status_code)
y = cy.get("/yonetim/")
kontrol("panel ana sayfasında Bildirimler görünüyor",
        "bildirim/bildirim" in y.content.decode())

print("— sipariş panelindeki toplu işlemler de bildirim gönderiyor")
# CC'nin sorduğu konu: panelden "teslim edildi" yapılınca müşteriye mesaj
# gitmiyordu. "Hazırlandı" işlemi ise çekimi atladığı için tamamen kaldırıldı.
sipP = siparis_ac()
Bildirim.objects.filter(siparis=sipP).delete()
y = c.get("/yonetim/siparis/siparis/")
govde = y.content.decode()
kontrol("'Hazırlandı olarak işaretle' panelden kalktı",
        "Hazırlandı olarak işaretle" not in govde)
kontrol("'Yola çıktı' işlemi duruyor", "Yola çıktı olarak işaretle" in govde)

c.post("/yonetim/siparis/siparis/",
       {"action": "yola_cikti_isaretle", "_selected_action": [str(sipP.pk)]})
kontrol("panelden yola çıktı → bildirim gitti",
        Bildirim.objects.filter(siparis=sipP, tur=Bildirim.Tur.YOLA_CIKTI,
                                durum=Bildirim.Durum.GONDERILDI).exists())
c.post("/yonetim/siparis/siparis/",
       {"action": "teslim_edildi_isaretle", "_selected_action": [str(sipP.pk)]})
kontrol("panelden teslim edildi → bildirim gitti",
        Bildirim.objects.filter(siparis=sipP, tur=Bildirim.Tur.TESLIM_EDILDI,
                                durum=Bildirim.Durum.GONDERILDI).exists())
sipP.refresh_from_db()
kontrol("sipariş teslim durumuna geçti", sipP.durum == Siparis.Durum.TESLIM_EDILDI,
        sipP.durum)

print()
print("SONUÇ: hepsi geçti" if hata == 0 else f"SONUÇ: {hata} hata")
