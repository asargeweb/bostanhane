"""
Bostanhane — örnek veri komutu

Bu dosya `core/management/commands/ornek_veri.py` olarak kaydedilir.
Çalıştırmak için:  python manage.py ornek_veri

Beyşehir mağazasını açar, hizmet alanını kurar ve 8 haftalık takvimi üretir.

**Hizmet alanı nasıl kuruluyor:**
- Merkez mahalleleri (13 tanesi) → **aktif**, haftada iki teslim günü var
- Köy kökenli mahalleler (57 tanesi) → **pasif** kayıt olarak eklenir; teslim günü yok,
  listede görünür ama sipariş almaz. Sırası geldiğinde panelden "aktif" kutucuğunu
  işaretlemek yeterli olacak.

Coğrafya verisi (il / ilçe / mahalle) burada oluşturulmaz; onu `cografya_yukle` yapar.
Eksikse bu komut onu kendisi çağırır.

Tekrar çalıştırılabilir; var olan kayıtları bozmaz. Panelden değiştirdiğiniz kapasite,
sıra ve aktiflik durumu korunur.
"""

from datetime import time

from django.core.management import call_command
from django.core.management.base import BaseCommand

from core.models import (
    Gun, HaftalikTeslimGunu, HizmetMahallesi, Ilce, Magaza, Mahalle, TeslimTakvimi,
)


# Haftalık rotalar. Her mahalle haftada iki kez ziyaret edilir.
# Çarşamba ve cumartesi de dolu; kargo paketleme günleri buna göre ayarlanacak.
ROTA_GUNLERI = {
    1: [Gun.PAZARTESI, Gun.PERSEMBE],
    2: [Gun.SALI, Gun.CUMA],
    3: [Gun.CARSAMBA, Gun.CUMARTESI],
}

# Merkez mahallesi → rota numarası. Sıralama kurye güzergâhına göre
# panelden değiştirilebilir; buradaki dağılım başlangıç taslağıdır.
MERKEZ_ROTALARI = {
    "muftu": 1,
    "hamidiye": 1,
    "dalyan": 1,
    "esentepe": 1,
    "beytepe": 1,

    "bahcelievler": 2,
    "haciakif": 2,
    "haciarmagan": 2,
    "evsat": 2,

    "yeni": 3,
    "icerisehir": 3,
    "avsar": 3,
    "yesilyurt": 3,
}

MERKEZ_KAPASITE = 40      # sipariş / gün
KIRSAL_KAPASITE = 20      # köy kökenli mahalleler açıldığında başlangıç değeri


class Command(BaseCommand):
    help = "Beyşehir mağazasını, merkez hizmet mahallelerini ve takvimi oluşturur."

    def handle(self, *args, **secenekler):
        # -- coğrafya hazır mı --------------------------------------------
        ilce = Ilce.objects.filter(il__ad="Konya", slug="beysehir").first()
        if ilce is None:
            self.stdout.write("Coğrafya verisi eksik, yükleniyor…")
            call_command("cografya_yukle", sessiz=True)
            ilce = Ilce.objects.filter(il__ad="Konya", slug="beysehir").first()
        if ilce is None:
            self.stdout.write(self.style.ERROR(
                "Beyşehir ilçesi bulunamadı. core/cografya_verisi.py dosyasını kontrol edin."))
            return

        # -- mağaza -------------------------------------------------------
        magaza, yeni = Magaza.objects.get_or_create(
            slug="beysehir",
            defaults={
                "ad": "Bostanhane Beyşehir",
                "il": ilce.il,
                "ilce": ilce,
                "adres": "Depo adresi girilecek",
                "telefon": "0332 000 00 00",
                "eposta": "beysehir@bostanhane.com",
            },
        )
        self.yaz(f"Mağaza: {magaza.ad} ({magaza.konum})", yeni)

        # -- merkez mahalleleri: aktif, teslim günleriyle -------------------
        self.stdout.write("\nMerkez mahalleleri (aktif):")
        toplam_takvim = 0
        sira = 0
        for mahalle_slug, rota in MERKEZ_ROTALARI.items():
            mahalle = Mahalle.objects.filter(ilce=ilce, slug=mahalle_slug).first()
            if mahalle is None:
                self.stdout.write(self.style.WARNING(
                    f"  ! {mahalle_slug} mahallesi Beyşehir listesinde yok, atlandı."))
                continue
            sira += 1

            hizmet, yeni = HizmetMahallesi.objects.get_or_create(
                magaza=magaza, mahalle=mahalle,
                defaults={"gunluk_kapasite": MERKEZ_KAPASITE, "sira": sira, "aktif": True},
            )
            gunler = ROTA_GUNLERI[rota]
            for gun in gunler:
                kural, yeni_kural = HaftalikTeslimGunu.objects.get_or_create(
                    hizmet_mahallesi=hizmet,
                    gun=gun,
                    defaults={
                        "teslim_baslangic": time(9, 0),
                        "teslim_bitis": time(18, 0),
                        "kesim_gun_farki": 1,
                        "kesim_saati": time(18, 0),
                    },
                )
                toplam_takvim += len(TeslimTakvimi.kural_uret(kural, hafta_sayisi=8))

            gun_metni = hizmet.teslim_gunleri_metni()
            self.yaz(f"  {mahalle.ad} — rota {rota} · {gun_metni}", yeni)

        # -- köy kökenli mahalleler: pasif kayıt ---------------------------
        # Neden hiç eklemeyip boş bırakmıyoruz: pasif kayıt panelde listede
        # görünür, açmak için tek kutucuk yeter. Sonra tek tek aramaktan iyidir.
        kirsal = Mahalle.objects.filter(ilce=ilce, tip=Mahalle.Tip.KIRSAL).order_by("ad")
        eklenen_kirsal = 0
        for konum, mahalle in enumerate(kirsal, start=101):
            _, yeni = HizmetMahallesi.objects.get_or_create(
                magaza=magaza, mahalle=mahalle,
                defaults={"gunluk_kapasite": KIRSAL_KAPASITE, "sira": konum, "aktif": False},
            )
            eklenen_kirsal += 1 if yeni else 0
        self.stdout.write(
            f"\nKöy kökenli mahalleler: {kirsal.count()} kayıt pasif "
            f"({eklenen_kirsal} yeni). Teslim günü tanımlanmadı."
        )

        # -- özet ----------------------------------------------------------
        aktif_adet = magaza.hizmet_mahalleleri.filter(aktif=True).count()
        pasif_adet = magaza.hizmet_mahalleleri.filter(aktif=False).count()
        self.stdout.write(self.style.SUCCESS(
            f"\nTamam. Takvime {toplam_takvim} teslim günü eklendi."
        ))
        self.stdout.write(
            f"Beyşehir'de {Mahalle.objects.filter(ilce=ilce).count()} mahalle tanımlı: "
            f"{aktif_adet} aktif, {pasif_adet} pasif."
        )
        self.stdout.write("Yönetim paneli: /yonetim/core/hizmetmahallesi/")

    def yaz(self, metin, yeni):
        if yeni:
            self.stdout.write(self.style.SUCCESS(f"+ {metin}"))
        else:
            self.stdout.write(f"· {metin} (zaten vardı)")
