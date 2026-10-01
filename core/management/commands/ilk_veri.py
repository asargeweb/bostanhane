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
            self.stdout.write("· Mağaza kaydı var, mağaza kurulumu atlandı.")
        else:
            self.stdout.write("Veritabanı boş. Beyşehir mağazası kuruluyor…")
            call_command("ornek_veri")

        # Ürünler burada OTOMATİK AKTARILMAZ.
        #
        # Karar: katalog panelden yönetiliyor. Ürün ve fiyat sürekli değişiyor;
        # dağıtım sırasında dosyadan veri basmak, panelde yapılan işi silme
        # riskini her deploy'a taşır. Katalog Ersin'in alanı.
        #
        # Taslak listeyi bir kez içeri almak isteyen `urun_yukle` komutunu elle
        # çalıştırır. O komut da panelde girilmiş fiyatlara dokunmaz.
        try:
            from katalog.models import Urun
        except ImportError:
            return
        adet = Urun.objects.count()
        if adet:
            self.stdout.write(f"· Katalogda {adet} ürün var.")
        else:
            self.stdout.write("· Katalog boş. Ürünler panelden girilecek "
                              "(/yonetim/katalog/urun/).")
