"""
Bostanhane — rol gruplarını kurar

Dosya yolu: hesaplar/management/commands/roller_kur.py
Çalıştırma:  python manage.py roller_kur

Her rol için Django grubunu oluşturur, yetkilerini `hesaplar/izinler.py`
dosyasındaki listeye göre günceller ve var olan kullanıcıları rollerine
uygun gruba bağlar.

Yeni uygulama eklendikçe bu komut tekrar çalıştırılır. Tekrar çalıştırmak
zararsızdır; grupları silmez, içeriğini yeniler.
"""

from django.core.management.base import BaseCommand

from hesaplar.izinler import gruplari_kur, kullanicilara_uygula


class Command(BaseCommand):
    help = "Rol gruplarını oluşturur ve yetkilerini güncelleyip kullanıcılara bağlar."

    def handle(self, *args, **secenekler):
        gruplari_kur(yaz=self.stdout.write)
        kullanicilara_uygula(yaz=self.stdout.write)
        self.stdout.write(self.style.SUCCESS("Roller güncel."))
