"""
Bostanhane — bildirim metinleri

Bu dosya `bildirim/metinler.py` olarak kaydedilir.

### İki ayrı metin, tek yerde

Her bildirimin **kısa** (SMS) ve **uzun** (e-posta) hâli var. İkisini yan yana
tutuyoruz ki biri değişince öteki unutulmasın.

### SMS neden bu kadar kısa

Türkçe karakter kullanan bir SMS'te sınır 70 karakter (bkz. `models.sms_parca_sayisi`).
70'i aşan her mesaj iki katına çıkıyor. Bu yüzden SMS metinleri **tek parçaya
sığacak şekilde** yazıldı ve `dene_bildirim.py` her birini ölçüyor — biri büyürse
test uyarıyor.

Kısalık müşteriye de iyi geliyor: telefonda okunan bir bildirimde ilk cümle dışında
hiçbir şey okunmuyor zaten.

### Ton

Söz vermiyoruz, bilgi veriyoruz. "Yakında geliyoruz" ya da "en taze ürünler" gibi
cümleler yok — müşteri sipariş bildirimi bekliyor, reklam değil.
"""

from django.conf import settings

from core.araclar import para_yaz

# SMS'in sonundaki imza. **Başlık (gönderen adı) BOSTANHANE olarak tahsis
# edilince bu boşaltılmalı:** telefonda mesaj zaten "BOSTANHANE" başlığıyla
# görünüyor, imza aynı bilgiyi tekrar edip her mesajda 12 karakter yiyor.
# Türkçe karakterli SMS'te sınır 70 olduğu için 12 karakter, mesajı tek
# parçada tutup tutmadığını belirliyor — yani doğrudan fatura demek.
#
# Başlık başka bir şirketin adıyla kalırsa imza yerinde dursun; müşteri
# mesajın kimden geldiğini başka türlü anlayamaz.
IMZA = str(getattr(settings, "SMS_IMZA", "Bostanhane") or "").strip()


def _imzala(metin):
    return f"{metin} {IMZA}".strip() if IMZA else metin


def _mahalle(siparis):
    takvim = siparis.teslim_takvimi
    return takvim.hizmet_mahallesi.mahalle.ad if takvim else "kargo"


def _tarih(siparis):
    takvim = siparis.teslim_takvimi
    return f"{takvim.tarih:%d.%m}" if takvim else ""


# ==========================================================================
# Her işlev (konu, sms, eposta) döndürür.
# ==========================================================================
def siparis_alindi(siparis):
    sms = _imzala(f"{siparis.numara} alındı. Kartınızda "
                  f"{para_yaz(siparis.provizyon_tutari)} bloke edildi.")
    eposta = (
        f"Merhaba {siparis.teslim_ad_soyad},\n\n"
        f"{siparis.numara} numaralı siparişinizi aldık.\n\n"
        f"Teslimat: {_tarih(siparis)} · {_mahalle(siparis)}\n"
        f"Tahmini tutar: {para_yaz(siparis.toplam)}\n"
        f"Kartınızda bloke edilen: {para_yaz(siparis.provizyon_tutari)}\n\n"
        f"Tartılı ürünlerde kesin tutar tartımdan sonra belli olur; kartınızdan "
        f"yalnızca kesin tutar çekilir, fazlası serbest bırakılır.\n\n"
        f"Siparişinizi hesabınızdan takip edebilirsiniz.\n\n{IMZA or 'Bostanhane'}")
    return f"{siparis.numara} siparişiniz alındı", sms, eposta


def kesim_yaklasti(siparis, kalan_dakika):
    saat = siparis.teslim_takvimi.kesim_zamani
    # Kısa tutuldu: 70 karakteri aşarsa iki SMS ücreti ödenir ve bu mesaj
    # bütün siparişlere gidiyor — en pahalı bildirim bu.
    # "bugün" çıkarıldı: mesaj zaten kesimden iki saat önce gidiyor, gün belli.
    # İmzayla birlikte tam 70 karakter — tek parça sınırı. `dene_bildirim.py`
    # bunu her çalıştırmada ölçüyor; metni uzatan olursa test uyarır.
    sms = _imzala(f"Siparişiniz {saat:%H.%M}'de kapanıyor. "
                  f"Eklemek istediğiniz var mı?")
    eposta = (
        f"Merhaba {siparis.teslim_ad_soyad},\n\n"
        f"{_tarih(siparis)} tarihli {_mahalle(siparis)} teslimatı için sipariş alımı "
        f"bugün {saat:%H.%M}'de kapanıyor.\n\n"
        f"Eklemek istediğiniz bir şey varsa o saate kadar sepetinize ekleyebilirsiniz. "
        f"Kapandıktan sonra sipariş değiştirilemiyor, çünkü ürünler sizin siparişinize "
        f"göre alınıyor.\n\n{IMZA or 'Bostanhane'}")
    return "Sipariş saatiniz kapanıyor", sms, eposta


def gun_kesildi(siparis):
    # Sipariş numarası çıkarıldı: müşteri tek siparişi olduğunu biliyor, numara
    # yer kaplıyor. "teslimatındasınız" yerine "teslimatı" — uzun mahalle adında
    # (Bahçelievler, Hacıarmağan) mesaj 70'i aşıp iki parçaya çıkıyordu.
    sms = _imzala(f"Siparişiniz kesinleşti. {_tarih(siparis)} "
                  f"{_mahalle(siparis)} teslimatı.")
    eposta = (
        f"Merhaba {siparis.teslim_ad_soyad},\n\n"
        f"{siparis.numara} numaralı siparişiniz kesinleşti.\n\n"
        f"Teslimat: {_tarih(siparis)} · {_mahalle(siparis)}\n\n"
        f"Ürünleriniz yarın sabah pazardan alınıp tartılacak. Tartımdan sonra kesin "
        f"tutarı size bildireceğiz.\n\n{IMZA or 'Bostanhane'}")
    return f"{siparis.numara} kesinleşti", sms, eposta


def urun_bulunamadi(siparis, kalemler):
    adlar = ", ".join(k.urun_adi for k in kalemler)
    dusulen = sum((k.birim_fiyat * k.siparis_miktari for k in kalemler), 0)
    sms = _imzala(f"{adlar} bulunamadı, {para_yaz(dusulen)} düşüldü.")
    satirlar = "\n".join(f"  · {k.urun_adi}" for k in kalemler)
    eposta = (
        f"Merhaba {siparis.teslim_ad_soyad},\n\n"
        f"{siparis.numara} numaralı siparişinizde bugün bulamadığımız ürünler:\n\n"
        f"{satirlar}\n\n"
        f"Bu ürünlerin bedeli ({para_yaz(dusulen)}) siparişinizden düşüldü; "
        f"kartınızdan tahsil edilmeyecek. Yerine başka bir ürün koymadık.\n\n{IMZA or 'Bostanhane'}")
    return "Siparişinizde bulunamayan ürün", sms, eposta


def yola_cikti(siparis):
    sms = _imzala(f"{siparis.numara} yola çıktı.")
    eposta = (
        f"Merhaba {siparis.teslim_ad_soyad},\n\n"
        f"{siparis.numara} numaralı siparişiniz yola çıktı.\n\n"
        f"Adres: {siparis.teslim_acik_adres}\n"
        f"Telefon: {siparis.teslim_telefon}\n\n"
        f"Kapıda ödeme alınmıyor; ödemeniz kartınızdan tahsil edilecek.\n\n{IMZA or 'Bostanhane'}")
    return f"{siparis.numara} yola çıktı", sms, eposta


def teslim_edildi(siparis):
    sms = _imzala(f"{siparis.numara} teslim edildi. Çekilen: "
                  f"{para_yaz(siparis.cekilen_tutar or siparis.toplam)}.")
    eposta = (
        f"Merhaba {siparis.teslim_ad_soyad},\n\n"
        f"{siparis.numara} numaralı siparişiniz teslim edildi.\n\n"
        f"Kartınızdan çekilen: {para_yaz(siparis.cekilen_tutar or siparis.toplam)}\n"
        f"Bloke edilen fazla tutar serbest bırakıldı; bankanıza göre birkaç iş günü "
        f"içinde hesabınıza yansır.\n\n"
        f"Bir sorun varsa hesabınızdaki sipariş sayfasından 24 saat içinde "
        f"bildirebilirsiniz.\n\n{IMZA or 'Bostanhane'}")
    return f"{siparis.numara} teslim edildi", sms, eposta


def siparis_iptal(siparis):
    sms = _imzala(f"{siparis.numara} iptal edildi. Kartınızdaki bloke çözüldü.")
    eposta = (
        f"Merhaba {siparis.teslim_ad_soyad},\n\n"
        f"{siparis.numara} numaralı siparişiniz iptal edildi. Kartınızda bloke edilen "
        f"tutar serbest bırakıldı; bankanıza göre birkaç iş günü içinde yansır.\n\n"
        f"{IMZA or 'Bostanhane'}")
    return f"{siparis.numara} iptal edildi", sms, eposta


def talep_karari(siparis, talep):
    # İmza bütün metin işlevlerinde aynı: (siparis, …). `islemler.gonder`
    # hepsini aynı şekilde çağırabilsin diye.
    if talep.iade_tutari:
        sms = _imzala(f"Bildiriminiz için {para_yaz(talep.iade_tutari)} "
                      f"kartınıza iade edildi.")
    else:
        sms = _imzala(f"{siparis.numara} bildiriminiz incelendi.")
    eposta = (
        f"Merhaba {siparis.teslim_ad_soyad},\n\n"
        f"{siparis.numara} numaralı siparişinizle ilgili bildiriminizi inceledik.\n\n"
        f"{talep.karar_notu}\n\n"
        + (f"İade edilen tutar: {para_yaz(talep.iade_tutari)}\n"
           f"Bankanıza göre birkaç iş günü içinde kartınıza yansır.\n\n"
           if talep.iade_tutari else "")
        + f"{IMZA or 'Bostanhane'}")
    return "Bildiriminize karar verildi", sms, eposta
