"""
Bostanhane — canlı ortamda ilk veriyi kurar.

Dosya yolu: core/management/commands/ilk_veri.py
Çalıştırma:  python manage.py ilk_veri

`ornek_veri` komutunun güvenli hali: veritabanında zaten bir mağaza varsa
hiçbir şey yapmaz. Bu yüzden Procfile içinde her dağıtımda çalışabilir —
elle sildiğiniz mahalleleri geri getirmez.

Neden gerekliydi: canlı veritabanı boş kurulduğunda "yakında" sayfası
mahalle listesini boş gösteriyordu.
"""

from django.core.management import call_command
from django.core.management.base import BaseCommand

from core.models import Il, Magaza


class Command(BaseCommand):
    help = "Coğrafyayı yükler; veritabanı boşsa Beyşehir mağazasını da kurar."

    def handle(self, *args, **secenekler):
        # Coğrafya her dağıtımda kontrol edilir: yeni il/ilçe eklediğimizde
        # canlıya kendiliğinden geçsin. Var olana dokunmaz.
        if Il.objects.count() < 81:
            self.stdout.write("Coğrafya verisi eksik, yükleniyor…")
            call_command("cografya_yukle", sessiz=True)
        else:
            self.stdout.write("· Coğrafya verisi yerinde.")

        if Magaza.objects.exists():
            self.stdout.write("· Mağaza kaydı var, ilk veri kurulumu atlandı.")
            return
        self.stdout.write("Veritabanı boş. Beyşehir mağazası kuruluyor…")
        call_command("ornek_veri")
