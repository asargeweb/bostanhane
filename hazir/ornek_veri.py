"""
Bostanhane — örnek veri komutu

Bu dosya `core/management/commands/ornek_veri.py` olarak kaydedilir.
Çalıştırmak için:  python manage.py ornek_veri

Beyşehir mağazasını, üç mahalleyi, teslim günlerini ve 8 haftalık takvimi oluşturur.
Tekrar çalıştırılabilir; var olan kayıtları bozmaz.
"""

from datetime import time
from django.core.management.base import BaseCommand
from core.models import Magaza, Mahalle, HaftalikTeslimGunu, TeslimTakvimi, Gun


class Command(BaseCommand):
    help = "Beyşehir mağazası ve pilot mahalleler için örnek veri oluşturur."

    def handle(self, *args, **secenekler):
        magaza, yeni = Magaza.objects.get_or_create(
            slug="beysehir",
            defaults={
                "ad": "Bostanhane Beyşehir",
                "il": "Konya",
                "ilce": "Beyşehir",
                "adres": "Depo adresi girilecek",
                "telefon": "0332 000 00 00",
                "eposta": "beysehir@bostanhane.com",
            },
        )
        self.yaz(f"Mağaza: {magaza.ad}", yeni)

        mahalleler = [
            # (ad, slug, kapasite, sıra, teslim günleri)
            ("Yeni Mahalle", "yeni-mahalle", 50, 1, [Gun.PAZARTESI, Gun.CUMA]),
            ("Müftü Mahallesi", "muftu", 45, 2, [Gun.SALI, Gun.CUMA]),
            ("Bahçelievler Mahallesi", "bahcelievler", 35, 3, [Gun.CARSAMBA]),
        ]

        toplam_takvim = 0
        for ad, slug, kapasite, sira, gunler in mahalleler:
            mahalle, yeni = Mahalle.objects.get_or_create(
                magaza=magaza,
                slug=slug,
                defaults={"ad": ad, "gunluk_kapasite": kapasite, "sira": sira},
            )
            self.yaz(f"  Mahalle: {mahalle.ad}", yeni)

            for gun in gunler:
                kural, yeni = HaftalikTeslimGunu.objects.get_or_create(
                    mahalle=mahalle,
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
        self.stdout.write("Yönetim paneli: http://127.0.0.1:8000/yonetim/")

    def yaz(self, metin, yeni):
        if yeni:
            self.stdout.write(self.style.SUCCESS(f"+ {metin}"))
        else:
            self.stdout.write(f"· {metin} (zaten vardı)")
