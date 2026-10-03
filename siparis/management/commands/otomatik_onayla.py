"""
Teslim edilip süre içinde onaylanmayan siparişleri onaylanmış sayar.

    python manage.py otomatik_onayla          # onaylar
    python manage.py otomatik_onayla --kuru   # ne yapacağını yazar, dokunmaz

Kesim servisiyle aynı 15 dakikalık turda çalışır
(`gunu_kes && otomatik_onayla`). Tekrar çalıştırılabilir: onaylanmış siparişe
bakmaz. Sorun bildirilmiş siparişe dokunmaz — mağaza karar verecek.

Otomatik onay müşterinin kusurlu ürün bildirme hakkını kaldırmaz; yalnızca
siparişi "kapanmış" sayar.
"""

from django.core.management.base import BaseCommand
from django.db import connection, transaction
from django.utils import timezone

from siparis.models import Siparis
from siparis.teslim_onayi import otomatik_onayla, otomatik_onaylanacaklar


class Command(BaseCommand):
    help = "Süresi dolan, onaysız teslim edilmiş siparişleri onaylanmış sayar."

    # gunu_kes'le aynı sebep: 15 dakikada bir çalışıyor, uyarı yığını gerçek hatayı gizler.
    requires_system_checks = []

    def add_arguments(self, ayristirici):
        ayristirici.add_argument("--kuru", action="store_true",
                                 help="Ne yapılacağını yazar, hiçbir şeyi değiştirmez.")

    def handle(self, *args, **secenekler):
        kuru = secenekler["kuru"]
        simdi = timezone.now()
        bekleyen = Siparis.objects.filter(durum=Siparis.Durum.TESLIM_EDILDI,
                                          onay_zamani__isnull=True).count()
        # DATABASE_URL tuzağını kayıtlarda ayırt etmek için (bkz. gunu_kes).
        self.stdout.write(f"{timezone.localtime(simdi):%d.%m.%Y %H.%M} · veritabanı: "
                          f"{connection.vendor} · onay bekleyen teslim: {bekleyen}")

        siparisler = otomatik_onaylanacaklar(simdi)
        if not siparisler:
            self.stdout.write("Otomatik onaylanacak sipariş yok.")
            return
        if kuru:
            self.stdout.write(self.style.WARNING("KURU ÇALIŞMA — hiçbir şey değiştirilmeyecek."))

        for siparis in siparisler:
            etiket = (f"{siparis.numara} · teslim {timezone.localtime(siparis.teslim_zamani):%d.%m %H.%M}"
                      f" · süre doldu {timezone.localtime(siparis.otomatik_onay_zamani):%d.%m %H.%M}")
            if kuru:
                self.stdout.write(f"  onaylanacak: {etiket}")
                continue
            with transaction.atomic():
                otomatik_onayla(siparis)
            self.stdout.write(self.style.SUCCESS(f"  onaylandı: {etiket}"))

        fiil = "onaylanacak" if kuru else "onaylandı"
        self.stdout.write(f"Toplam: {len(siparisler)} sipariş {fiil}.")
