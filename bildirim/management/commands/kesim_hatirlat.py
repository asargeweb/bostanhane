"""
Bostanhane — kesim saati hatırlatması

Bu dosya `bildirim/management/commands/kesim_hatirlat.py` olarak kaydedilir.

Kesim saatine az kalan teslim günlerindeki müşterilere *"bugün kapanıyor, eklemek
istediğiniz var mı"* mesajı gönderir.

### Niye bu mesaj önemli

Diğer bildirimler müşteriyi bilgilendiriyor; bu mesaj **satış yapıyor.** Sepetinde
400 ₺'lik ürün olan müşteri "iki saat sonra kapanıyor" mesajını alınca minimum
sepete ulaşmak için ürün ekliyor. Pilotta ciroya en çok dokunacak tek bildirim bu.

### Zamanlama

Mevcut `kesim` servisi 15 dakikada bir çalışıyor. Komut da oraya eklenecek:

    python manage.py gunu_kes && python manage.py otomatik_onayla && python manage.py kesim_hatirlat

Pencere mantığı: kesime kalan süre `--once` dakikasının altına düştüğünde gönderilir.
15 dakikada bir çalıştığı için mesaj kesimden en fazla 15 dakika sapmayla gider.
Çift gönderim koruması bildirim katmanında (sipariş + tür başına tek kayıt), yani
komut kaç kez çalışırsa çalışsın müşteri tek mesaj alır.
"""

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import connection
from django.utils import timezone

from bildirim.islemler import kesim_yaklasti_bildir
from core.models import TeslimTakvimi
from siparis.models import Siparis


class Command(BaseCommand):
    help = "Kesim saati yaklaşan siparişlere hatırlatma gönderir."
    requires_system_checks = []          # 15 dakikada bir çalışıyor, kayıt temiz kalsın

    def add_arguments(self, ayristirici):
        ayristirici.add_argument(
            "--once", type=int, default=120,
            help="Kesimden kaç dakika önce hatırlatılsın (varsayılan 120).")
        ayristirici.add_argument(
            "--kuru", action="store_true",
            help="Hiçbir şey göndermez, ne göndereceğini yazar.")

    def handle(self, *args, **secenekler):
        once = secenekler["once"]
        kuru = secenekler["kuru"]
        simdi = timezone.now()

        self.stdout.write(
            f"{timezone.localtime(simdi):%d.%m.%Y %H.%M} · "
            f"veritabanı: {connection.vendor} · hatırlatma penceresi: {once} dk")
        if kuru:
            self.stdout.write(self.style.WARNING(
                "KURU ÇALIŞMA — hiçbir şey gönderilmeyecek."))

        # Kesime `once` dakikadan az kalmış, hâlâ açık günler.
        takvimler = TeslimTakvimi.objects.filter(
            durum=TeslimTakvimi.Durum.ACIK,
            kesim_zamani__gt=simdi,
            kesim_zamani__lte=simdi + timedelta(minutes=once),
        ).select_related("hizmet_mahallesi__mahalle")

        if not takvimler:
            self.stdout.write("Hatırlatılacak gün yok.")
            return

        toplam_sip, toplam_msj = 0, 0
        for takvim in takvimler:
            kalan = int((takvim.kesim_zamani - simdi).total_seconds() // 60)
            siparisler = (takvim.siparisler
                          .filter(durum=Siparis.Durum.ALINDI)
                          .select_related("uye", "magaza",
                                          "teslim_takvimi__hizmet_mahallesi__mahalle"))
            self.stdout.write(
                f"  {takvim.hizmet_mahallesi.mahalle.ad} · "
                f"{takvim.tarih:%d.%m.%Y} · kesime {kalan} dk · "
                f"{siparisler.count()} sipariş")
            for siparis in siparisler:
                toplam_sip += 1
                if kuru:
                    self.stdout.write(f"    → {siparis.numara} ({siparis.teslim_telefon})")
                    continue
                gonderilen = kesim_yaklasti_bildir(siparis, kalan)
                toplam_msj += sum(1 for b in gonderilen if b.gonderildi_mi)
                if gonderilen:
                    self.stdout.write(
                        f"    → {siparis.numara}: "
                        + ", ".join(f"{b.get_kanal_display()} {b.get_durum_display()}"
                                    for b in gonderilen))
                else:
                    # Daha önce gönderilmiş; çift gönderim koruması çalıştı.
                    self.stdout.write(f"    · {siparis.numara}: zaten gönderilmiş")

        self.stdout.write(self.style.SUCCESS(
            f"Toplam: {toplam_sip} sipariş, "
            f"{toplam_msj} mesaj {'gönderilecek' if kuru else 'gönderildi'}."))
