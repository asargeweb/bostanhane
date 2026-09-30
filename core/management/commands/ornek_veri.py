"""
Bostanhane — örnek veri komutu

Bu dosya `core/management/commands/ornek_veri.py` olarak kaydedilir.
Çalıştırmak için:  python manage.py ornek_veri

Beyşehir mağazasını açar, pilot mahalleleri hizmet alanına ekler, teslim
günlerini tanımlar ve 8 haftalık takvimi üretir.

Coğrafya verisi (il / ilçe / mahalle) burada oluşturulmaz; onu `cografya_yukle`
yapar. Bu komut eksikse onu kendisi çağırır.

Tekrar çalıştırılabilir; var olan kayıtları bozmaz.
"""

from datetime import time

from django.core.management import call_command
from django.core.management.base import BaseCommand

from core.models import (
    Gun, HaftalikTeslimGunu, HizmetMahallesi, Il, Ilce, Magaza, Mahalle, TeslimTakvimi,
)


# Pilot hizmet alanı: (mahalle kısa adı, günlük kapasite, sıra, teslim günleri)
PILOT_MAHALLELER = [
    ("yeni", 50, 1, [Gun.PAZARTESI, Gun.CUMA]),
    ("muftu", 45, 2, [Gun.SALI, Gun.CUMA]),
    ("bahcelievler", 35, 3, [Gun.CARSAMBA]),
]


class Command(BaseCommand):
    help = "Beyşehir mağazasını ve pilot hizmet mahallelerini oluşturur."

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

        # -- hizmet mahalleleri ve teslim günleri -------------------------
        toplam_takvim = 0
        for mahalle_slug, kapasite, sira, gunler in PILOT_MAHALLELER:
            mahalle = Mahalle.objects.filter(ilce=ilce, slug=mahalle_slug).first()
            if mahalle is None:
                self.stdout.write(self.style.WARNING(
                    f"  ! {mahalle_slug} mahallesi Beyşehir listesinde yok, atlandı."))
                continue

            hizmet, yeni = HizmetMahallesi.objects.get_or_create(
                magaza=magaza, mahalle=mahalle,
                defaults={"gunluk_kapasite": kapasite, "sira": sira},
            )
            self.yaz(f"  Hizmet mahallesi: {mahalle.ad}", yeni)

            for gun in gunler:
                kural, yeni = HaftalikTeslimGunu.objects.get_or_create(
                    hizmet_mahallesi=hizmet,
                    gun=gun,
                    defaults={
                        "teslim_baslangic": time(9, 0),
                        "teslim_bitis": time(18, 0),
                        "kesim_gun_farki": 1,
                        "kesim_saati": time(18, 0),
                    },
                )
                self.yaz(f"    Teslim günü: {kural.get_gun_display()}", yeni)
                toplam_takvim += len(TeslimTakvimi.kural_uret(kural, hafta_sayisi=8))

        self.stdout.write(self.style.SUCCESS(
            f"\nTamam. Takvime {toplam_takvim} teslim günü eklendi."
        ))
        self.stdout.write(
            f"Beyşehir'de {Mahalle.objects.filter(ilce=ilce).count()} mahalle tanımlı, "
            f"{magaza.hizmet_mahalleleri.count()} tanesine hizmet veriliyor."
        )
        self.stdout.write("Yönetim paneli: /yonetim/")

    def yaz(self, metin, yeni):
        if yeni:
            self.stdout.write(self.style.SUCCESS(f"+ {metin}"))
        else:
            self.stdout.write(f"· {metin} (zaten vardı)")
