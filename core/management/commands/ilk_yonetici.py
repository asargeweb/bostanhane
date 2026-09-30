"""
Bostanhane — canlı ortamda ilk yönetici hesabını açar.

Dosya yolu: core/management/commands/ilk_yonetici.py
Çalıştırma:  python manage.py ilk_yonetici

Railway'de terminal açmak zahmetli olduğu için hesabı ortam değişkenlerinden okuyoruz.
Railway panelinde şu üç değişkeni tanımlayın:
    YONETICI_KULLANICI, YONETICI_EPOSTA, YONETICI_SIFRE

Hesap zaten varsa dokunmaz. Hesabı açtıktan sonra şifreyi panelden değiştirin
ve bu değişkenleri Railway'den silin.
"""

import os
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Ortam değişkenlerinden ilk süper kullanıcıyı oluşturur."

    def handle(self, *args, **secenekler):
        Kullanici = get_user_model()

        kullanici_adi = os.environ.get("YONETICI_KULLANICI", "yonetici")
        eposta = os.environ.get("YONETICI_EPOSTA", "")
        sifre = os.environ.get("YONETICI_SIFRE", "")

        if not sifre:
            self.stdout.write(self.style.WARNING(
                "YONETICI_SIFRE tanımlı değil; hesap oluşturulmadı."
            ))
            return

        if Kullanici.objects.filter(username=kullanici_adi).exists():
            self.stdout.write(f"· {kullanici_adi} zaten var, dokunulmadı.")
            return

        Kullanici.objects.create_superuser(
            username=kullanici_adi, email=eposta, password=sifre
        )
        self.stdout.write(self.style.SUCCESS(
            f"+ Yönetici hesabı oluşturuldu: {kullanici_adi}\n"
            "  Giriş yaptıktan sonra şifrenizi değiştirin ve "
            "YONETICI_SIFRE değişkenini Railway'den silin."
        ))
