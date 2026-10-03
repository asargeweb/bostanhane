"""
Bostanhane — mahalle nüfuslarını yükler

Bu dosya `core/management/commands/nufus_yukle.py` olarak kaydedilir.

Kullanım:

    python manage.py nufus_yukle            # yükler
    python manage.py nufus_yukle --kuru     # ne yapacağını yazar, yapmaz

Veri `core/nufus_verisi.py`'de; kaynağı ve yılı orada yazılı. Komut yalnızca
eşleşen mahalleleri günceller — listede olmayan mahalleye sayı **uydurmaz**,
"eşleşmedi" diye raporlar.
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from core.araclar import turkce_slug
from core.models import Ilce, Mahalle
from core.nufus_verisi import NUFUSLAR


class Command(BaseCommand):
    help = "Mahalle nüfuslarını core/nufus_verisi.py'den yükler."

    def add_arguments(self, ayristirici):
        ayristirici.add_argument(
            "--kuru", action="store_true",
            help="Hiçbir şey değiştirmez, ne yapacağını yazar.")

    def handle(self, *args, **secenekler):
        kuru = secenekler["kuru"]
        if kuru:
            self.stdout.write(self.style.WARNING(
                "KURU ÇALIŞMA — hiçbir şey değiştirilmeyecek."))

        toplam_guncel, toplam_eksik = 0, []
        for ilce_slug, (kaynak, yil, tablo, ayri) in NUFUSLAR.items():
            ilce = Ilce.objects.filter(slug=ilce_slug).first()
            if ilce is None:
                self.stdout.write(self.style.ERROR(
                    f"  ! ilçe bulunamadı: {ilce_slug} — atlandı"))
                continue

            # Mahalleleri slug'a göre eşleştiriyoruz: "Hacıakif" ile "Hacıakıf"
            # gibi yazım farkları slug'da aynıya düşüyor.
            mahalleler = {m.slug: m for m in ilce.mahalleler.all()}
            eslesen = {}
            for ad, nufus in tablo.items():
                mahalle = mahalleler.get(turkce_slug(ad))
                if mahalle is None:
                    self.stdout.write(self.style.WARNING(
                        f"  ? listede var, veritabanında yok: {ad}"))
                    continue
                eslesen[mahalle.pk] = (mahalle, nufus, yil, kaynak)

            # Kendi yılı ve kaynağı olan tek tek eklemeler
            for ad, (nufus, ayri_yil, ayri_kaynak) in ayri.items():
                mahalle = mahalleler.get(turkce_slug(ad))
                if mahalle is None:
                    self.stdout.write(self.style.WARNING(
                        f"  ? listede var, veritabanında yok: {ad}"))
                    continue
                eslesen[mahalle.pk] = (mahalle, nufus, ayri_yil, ayri_kaynak)

            eksik = [m.ad for s, m in mahalleler.items() if m.pk not in eslesen]
            toplam_eksik.extend(f"{ilce.ad} · {ad}" for ad in sorted(eksik))

            if not kuru:
                with transaction.atomic():
                    for mahalle, nufus, m_yil, m_kaynak in eslesen.values():
                        mahalle.nufus = nufus
                        mahalle.nufus_yili = m_yil
                        mahalle.nufus_kaynagi = m_kaynak
                        mahalle.save(update_fields=["nufus", "nufus_yili",
                                                    "nufus_kaynagi"])
            toplam_guncel += len(eslesen)
            self.stdout.write(
                f"{ilce.ad}: {len(eslesen)} mahalleye nüfus "
                f"{'yazılacak' if kuru else 'yazıldı'} ({kaynak}).")

        if toplam_eksik:
            self.stdout.write(self.style.WARNING(
                f"\nNüfusu olmayan {len(toplam_eksik)} mahalle "
                f"(listede yoklar, boş bırakıldı):"))
            for ad in toplam_eksik:
                self.stdout.write(f"  · {ad}")
            self.stdout.write(
                "Bu mahallelerin nüfusu TÜİK'ten bulunup "
                "core/nufus_verisi.py'ye eklenebilir.")

        self.stdout.write(self.style.SUCCESS(
            f"\nToplam: {toplam_guncel} mahalle "
            f"{'güncellenecek' if kuru else 'güncellendi'}."))
