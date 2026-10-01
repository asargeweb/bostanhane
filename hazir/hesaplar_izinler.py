"""
Bostanhane — rol yetkileri

Bu dosya `hesaplar/izinler.py` olarak kaydedilir.

Django'da "panele girebilir" (is_staff) ile "şunu yapabilir" (yetki) ayrı şeylerdir.
İkinci kısmı **grup** ile veriyoruz: her rolün bir grubu var, grubun içinde o rolün
yapabileceği işlerin listesi duruyor.

Neden grup? Personel sayısı arttığında her kişi için kırk kutucuk işaretlemek
gerekmesin. Rol seçilince grup otomatik bağlanıyor.

Yeni bir uygulama eklediğimizde (katalog, siparis…) izin listesine satır ekleyip
`python manage.py roller_kur` çalıştırmak yeterli olacak.

Süper admin bu listede yok: `is_superuser` bütün yetkileri baştan verir.
"""

from .models import Rol


# Kısaltmalar: v=görme, e=ekleme, d=değiştirme, s=silme
TUMU = ["view", "add", "change", "delete"]
GOR_EKLE_DEGISTIR = ["view", "add", "change"]
SADECE_GOR = ["view"]


MAGAZA_YONETICISI = {
    "core.magaza": SADECE_GOR,                # mağazayı süper admin açar
    "core.il": SADECE_GOR,                    # coğrafya resmî veri, değiştirilmez
    "core.ilce": SADECE_GOR,
    "core.mahalle": SADECE_GOR,
    "core.satisayarlari": ["view", "change"],  # eşikleri panelden kendi ayarlar
    "core.hizmetmahallesi": TUMU,             # hangi mahalleye gidileceğine o karar verir
    "core.haftalikteslimgunu": TUMU,
    "core.teslimtakvimi": GOR_EKLE_DEGISTIR,
    "core.ilgikaydi": ["view", "change"],
    "katalog.kategori": GOR_EKLE_DEGISTIR,
    "katalog.urun": GOR_EKLE_DEGISTIR,        # ürün tanımı; silme süper adminde
    "katalog.magazaurun": TUMU,               # fiyat ve stok onun işi
    "katalog.birim": GOR_EKLE_DEGISTIR,       # "tepsi", "kasa" gibi birimi kendi ekler
    "katalog.stokhareketi": SADECE_GOR,       # defter; hareket Ürünler listesinden girilir
    "hesaplar.kullanici": GOR_EKLE_DEGISTIR,  # personel ve üye ekler, silmez
    "hesaplar.adres": TUMU,
}

PAKETLEME = {
    "core.satisayarlari": SADECE_GOR,
    "katalog.urun": SADECE_GOR,
    "katalog.magazaurun": SADECE_GOR,
    "katalog.birim": SADECE_GOR,
    "katalog.stokhareketi": SADECE_GOR,
    "core.mahalle": SADECE_GOR,
    "core.hizmetmahallesi": SADECE_GOR,
    "core.teslimtakvimi": SADECE_GOR,
    "hesaplar.adres": SADECE_GOR,
}

KURYE = {
    "katalog.urun": SADECE_GOR,
    "core.mahalle": SADECE_GOR,
    "core.hizmetmahallesi": SADECE_GOR,
    "core.teslimtakvimi": SADECE_GOR,
    "hesaplar.adres": SADECE_GOR,
}


# Rol → (grup adı, izin listesi)
ROL_IZINLERI = {
    Rol.MAGAZA_YONETICISI: ("Mağaza Yöneticisi", MAGAZA_YONETICISI),
    Rol.PAKETLEME: ("Paketleme Elemanı", PAKETLEME),
    Rol.KURYE: ("Kurye", KURYE),
}

# Rol → grup adı (kullanıcı kaydedilirken hangi gruba bağlanacağı)
ROL_GRUP_ADLARI = {rol: ad for rol, (ad, _) in ROL_IZINLERI.items()}


def gruplari_kur(yaz=None):
    """
    Rol gruplarını oluşturur ve izinlerini güncel hale getirir.
    `roller_kur` komutu bunu çağırır. Var olan grubu siler değil, içeriğini yeniler.

    Henüz oluşturulmamış modellerin izinleri sessizce atlanır; böylece bu liste
    ileride eklenecek uygulamaların satırlarını da taşıyabilir.
    """
    from django.contrib.auth.models import Group, Permission

    for rol, (grup_adi, izin_haritasi) in ROL_IZINLERI.items():
        grup, yeni = Group.objects.get_or_create(name=grup_adi)
        izinler = []
        eksik = []
        for hedef, eylemler in izin_haritasi.items():
            uygulama, model = hedef.split(".")
            for eylem in eylemler:
                kod = f"{eylem}_{model}"
                izin = Permission.objects.filter(
                    content_type__app_label=uygulama, codename=kod
                ).first()
                if izin is None:
                    eksik.append(f"{uygulama}.{kod}")
                else:
                    izinler.append(izin)
        grup.permissions.set(izinler)
        if yaz:
            yaz(f"{'+' if yeni else '·'} {grup_adi}: {len(izinler)} yetki")
            for e in eksik:
                yaz(f"    ! henüz yok, atlandı: {e}")


def kullanicilara_uygula(yaz=None):
    """Var olan bütün kullanıcıların grubunu rolüne göre yeniden bağlar."""
    from django.contrib.auth import get_user_model

    sayac = 0
    for kullanici in get_user_model().objects.all():
        kullanici.rol_grubunu_uygula()
        sayac += 1
    if yaz:
        yaz(f"{sayac} kullanıcının grubu rolüne göre ayarlandı.")
