"""
Kesim saati geçmiş ve hâlâ açık duran teslim günlerini keser.

    python manage.py gunu_kes          # keser
    python manage.py gunu_kes --kuru   # ne keseceğini yazar, dokunmaz

Neden komut: kimse günü elle kesmezse sipariş akmaya devam eder, alım listesi
hiç kesinleşmez — işin sessizce bozulabileceği tek yer burası. Railway'de
zamanlanmış görev olarak (ör. her 15 dakikada bir) çalışacak.

Tekrar çalıştırılabilir: yalnızca ACIK günlere bakar. Zamanlanmış görev iki kez
tetiklenirse ikinci çalıştırma "kesilecek gün yok" der, hata vermez. Her gün
kendi işleminde kesilir; biri hata verirse ötekiler yine kesilir.
"""

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from core.models import TeslimTakvimi
from siparis.models import Siparis, gunu_kes


class Command(BaseCommand):
    help = "Kesim saati geçmiş, hâlâ açık teslim günlerini keser."

    def add_arguments(self, ayristirici):
        ayristirici.add_argument("--kuru", action="store_true",
                                 help="Ne yapılacağını yazar, hiçbir şeyi değiştirmez.")

    def handle(self, *args, **secenekler):
        kuru = secenekler["kuru"]
        simdi = timezone.now()
        gunler = (TeslimTakvimi.objects
                  .filter(durum=TeslimTakvimi.Durum.ACIK, kesim_zamani__lte=simdi)
                  .select_related("hizmet_mahallesi__mahalle", "hizmet_mahallesi__magaza")
                  .order_by("kesim_zamani", "hizmet_mahallesi__sira"))

        if not gunler:
            self.stdout.write(f"{timezone.localtime(simdi):%d.%m.%Y %H.%M} · Kesilecek gün yok.")
            return

        if kuru:
            self.stdout.write(self.style.WARNING("KURU ÇALIŞMA — hiçbir şey değiştirilmeyecek."))

        gun_adedi = siparis_adedi = 0
        for takvim in gunler:
            bekleyen = takvim.siparisler.filter(durum=Siparis.Durum.ALINDI).count()
            etiket = (f"{takvim.hizmet_mahallesi.magaza.ad} · {takvim.hizmet_mahallesi.mahalle.ad} · "
                      f"{takvim.tarih:%d.%m.%Y} (kesim {timezone.localtime(takvim.kesim_zamani):%d.%m %H.%M})")
            if kuru:
                self.stdout.write(f"  kesilecek: {etiket} — {bekleyen} sipariş")
                gun_adedi += 1
                siparis_adedi += bekleyen
                continue
            try:
                with transaction.atomic():
                    adet = gunu_kes(takvim)
            except ValidationError as hata:
                # Bu arada biri elle kesmiş olabilir; atla, ötekilere devam et.
                self.stdout.write(self.style.WARNING(f"  atlandı: {etiket} — {' '.join(hata.messages)}"))
                continue
            self.stdout.write(self.style.SUCCESS(f"  kesildi: {etiket} — {adet} sipariş"))
            gun_adedi += 1
            siparis_adedi += adet

        fiil = "kesilecek" if kuru else "kesildi"
        self.stdout.write(f"Toplam: {gun_adedi} gün {fiil}, {siparis_adedi} sipariş toplamaya "
                          f"{'açılacak' if kuru else 'açıldı'}.")
