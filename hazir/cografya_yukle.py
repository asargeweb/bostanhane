"""
Bostanhane — il / ilçe / mahalle verisini yükler

Dosya yolu: core/management/commands/cografya_yukle.py
Çalıştırma:  python manage.py cografya_yukle

Listeler `core/cografya_verisi.py` dosyasında. Yeni il veya ilçe eklemek için
orayı düzenleyip bu komutu tekrar çalıştırmak yeterli.

Tekrar çalıştırılabilir: var olan kayıtlara dokunmaz, yalnızca eksikleri ekler.
Bu yüzden canlı sunucuda her dağıtımda çalışması sorun değil.
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from core.araclar import turkce_slug
from core.cografya_verisi import ILLER, ILCELER, MAHALLELER
from core.models import Il, Ilce, Mahalle


class Command(BaseCommand):
    help = "81 ili, tanımlı ilçeleri ve mahalleleri veritabanına yükler."

    def add_arguments(self, ayristirici):
        ayristirici.add_argument(
            "--sessiz", action="store_true",
            help="Yalnızca özet yaz, tek tek kayıt adı yazma.")

    @transaction.atomic
    def handle(self, *args, **secenekler):
        self.sessiz = secenekler["sessiz"]
        eklenen = {"il": 0, "ilce": 0, "mahalle": 0}

        # -- iller ---------------------------------------------------------
        iller = {}
        for plaka, ad in ILLER:
            il, yeni = Il.objects.get_or_create(
                plaka=plaka, defaults={"ad": ad, "slug": turkce_slug(ad)})
            iller[ad] = il
            eklenen["il"] += 1 if yeni else 0
        self.stdout.write(f"İl: {len(ILLER)} kayıt işlendi, {eklenen['il']} yeni.")

        # -- ilçeler -------------------------------------------------------
        ilceler = {}
        for il_adi, ilce_adlari in ILCELER.items():
            il = iller.get(il_adi)
            if il is None:
                self.stdout.write(self.style.WARNING(f"! {il_adi} ili listede yok, atlandı."))
                continue
            for ilce_adi in ilce_adlari:
                ilce, yeni = Ilce.objects.get_or_create(
                    il=il, slug=turkce_slug(ilce_adi), defaults={"ad": ilce_adi})
                ilceler[f"{il_adi} / {ilce_adi}"] = ilce
                eklenen["ilce"] += 1 if yeni else 0
                self.ayrinti(f"  {ilce}", yeni)
        self.stdout.write(f"İlçe: {eklenen['ilce']} yeni.")

        # -- mahalleler ----------------------------------------------------
        for anahtar, veri in MAHALLELER.items():
            ilce = ilceler.get(anahtar)
            if ilce is None:
                self.stdout.write(self.style.WARNING(f"! {anahtar} ilçesi bulunamadı, atlandı."))
                continue
            posta_kodu = veri.get("posta_kodu", "")
            for tip, alan in ((Mahalle.Tip.MERKEZ, "merkez"), (Mahalle.Tip.KIRSAL, "kirsal")):
                for mahalle_adi in veri.get(alan, []):
                    mahalle, yeni = Mahalle.objects.get_or_create(
                        ilce=ilce, slug=turkce_slug(mahalle_adi),
                        defaults={"ad": mahalle_adi, "tip": tip, "posta_kodu": posta_kodu})
                    eklenen["mahalle"] += 1 if yeni else 0
                    self.ayrinti(f"    {mahalle.ad} ({mahalle.get_tip_display()})", yeni)
            toplam = ilce.mahalleler.count()
            self.stdout.write(f"{anahtar}: {toplam} mahalle.")

        self.stdout.write(self.style.SUCCESS(
            f"\nTamam. Yeni: {eklenen['il']} il, {eklenen['ilce']} ilçe, "
            f"{eklenen['mahalle']} mahalle."
        ))

    def ayrinti(self, metin, yeni):
        if self.sessiz or not yeni:
            return
        self.stdout.write(self.style.SUCCESS(f"+{metin}"))
