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

        self.birimleri_kur()

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

    # ----------------------------------------------------------------------
    def birimleri_kur(self):
        """
        Ölçü birimlerini güvenceller.

        Ürünlerin kendisi panelden giriliyor (yukarıdaki karar), ama **birim**
        öyle değil: birim ürünün ön koşulu. Birimler yokken `urun_yukle`
        hiçbir satırı yükleyemiyor, her ürün için "kilogram birimi tanımlı
        değil" diyip geçiyor — boş bir veritabanında kurulum, panele girip
        elle altı birim eklenene kadar duruyordu ve sebebi hemen anlaşılmıyordu.

        `kesirli` alanı önemli: tartılı ürün (domates) yalnızca kesirli bir
        birimle satılabiliyor, "1,5 demet maydanoz" ise reddedilmeli.

        Var olanı değiştirmiyor — panelden eklenmiş birim ya da düzeltilmiş
        kısaltma her dağıtımda geri alınmasın.
        """
        try:
            from katalog.models import Birim
        except ImportError:                      # katalog henüz kurulmamış
            return

        # Adlar ve kısaltmalar canlıdaki yazımla birebir aynı — aksi hâlde
        # "Kilogram" varken "kilogram" açılmaya çalışılıyor ve `kisaltma` tek
        # olmak zorunda olduğu için komut çöküyor.
        birimler = [
            ("Kilogram", "kg", True),
            ("Gram", "g", False),
            ("Litre", "lt", True),
            ("Adet", "adet", False),
            ("Demet", "demet", False),
            ("Paket", "paket", False),
            ("Kavanoz", "kavanoz", False),
            ("Şişe", "şişe", False),
            ("Kutu", "kutu", False),
        ]
        yeni = 0
        for sira, (ad, kisaltma, kesirli) in enumerate(birimler, start=1):
            # Hem ada hem kısaltmaya bakıyoruz, ikisi de tek olmak zorunda.
            # Büyük-küçük harf farkı yok sayılıyor: panelde "KG" yazılmış
            # olabilir, onun üstüne ikinci bir kayıt açmayalım.
            if Birim.objects.filter(ad__iexact=ad).exists():
                continue
            if Birim.objects.filter(kisaltma__iexact=kisaltma).exists():
                continue
            Birim.objects.create(ad=ad, kisaltma=kisaltma, kesirli=kesirli, sira=sira)
            yeni += 1
        if yeni:
            self.stdout.write(f"{yeni} birim eklendi (toplam {Birim.objects.count()}).")
        else:
            self.stdout.write(f"· {Birim.objects.count()} birim yerinde.")
