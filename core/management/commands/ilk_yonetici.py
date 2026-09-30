"""
Bostanhane — canlı ortamda ilk yönetici hesabını açar.

Dosya yolu: core/management/commands/ilk_yonetici.py
Çalıştırma:  python manage.py ilk_yonetici

Railway'de terminal açmak zahmetli olduğu için hesabı ortam değişkenlerinden
okuyoruz. Railway panelinde şu üç değişkeni tanımlayın:

    YONETICI_TELEFON   → 10 hane, başında sıfır olmadan. Örnek: 5321112233
    YONETICI_AD        → Ad Soyad
    YONETICI_SIFRE     → güçlü bir şifre

Hesap zaten varsa dokunmaz. Hesabı açtıktan sonra şifreyi panelden değiştirin
ve YONETICI_SIFRE değişkenini Railway'den silin.
"""

import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Ortam değişkenlerinden ilk süper admin hesabını oluşturur."

    def handle(self, *args, **secenekler):
        Kullanici = get_user_model()

        telefon = (os.environ.get("YONETICI_TELEFON") or "").strip()
        ad_soyad = (os.environ.get("YONETICI_AD") or "Bostanhane Yöneticisi").strip()
        eposta = (os.environ.get("YONETICI_EPOSTA") or "").strip()
        sifre = os.environ.get("YONETICI_SIFRE") or ""

        if not telefon or not sifre:
            self.stdout.write(self.style.WARNING(
                "YONETICI_TELEFON veya YONETICI_SIFRE tanımlı değil; hesap oluşturulmadı."
            ))
            return

        # Numara '0532...' ya da '+90532...' girilmiş olabilir; modelin
        # düzeltme yardımcısı hepsini aynı biçime indiriyor.
        from hesaplar.models import telefon_duzelt
        telefon = telefon_duzelt(telefon)

        if Kullanici.objects.filter(telefon=telefon).exists():
            self.stdout.write(f"· {telefon} zaten kayıtlı, dokunulmadı.")
            return

        Kullanici.objects.create_superuser(
            telefon=telefon, password=sifre, ad_soyad=ad_soyad, eposta=eposta
        )
        self.stdout.write(self.style.SUCCESS(
            f"+ Süper admin oluşturuldu: {ad_soyad} ({telefon})\n"
            "  Giriş yaptıktan sonra şifrenizi değiştirin ve "
            "YONETICI_SIFRE değişkenini Railway'den silin."
        ))
