"""
Bostanhane — örnek veri komutu

Bu dosya `core/management/commands/ornek_veri.py` olarak kaydedilir.
Çalıştırmak için:  python manage.py ornek_veri

Beyşehir mağazasını açar, hizmet alanını kurar ve 8 haftalık takvimi üretir.

**Hizmet alanı nasıl kuruluyor:**
- Merkez mahalleleri (13 tanesi) → **aktif**, haftada iki teslim günü var
- Köy kökenli mahalleler (57 tanesi) → **pasif** kayıt olarak eklenir; teslim günü yok,
  listede görünür ama sipariş almaz. Sırası geldiğinde panelden "aktif" kutucuğunu
  işaretlemek yeterli olacak.

Coğrafya verisi (il / ilçe / mahalle) burada oluşturulmaz; onu `cografya_yukle` yapar.
Eksikse bu komut onu kendisi çağırır.

Tekrar çalıştırılabilir; var olan kayıtları bozmaz. Panelden değiştirdiğiniz kapasite,
sıra ve aktiflik durumu korunur.
"""

from datetime import time

from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.utils import timezone

from core.models import (
    Gun, HaftalikTeslimGunu, HizmetMahallesi, Ilce, Magaza, Mahalle,
    SatisAyarlari, TeslimTakvimi,
)


# Haftalık rotalar. Her mahalle haftada iki kez ziyaret edilir.
# Çarşamba ve cumartesi de dolu; kargo paketleme günleri buna göre ayarlanacak.
# Haftalık rota — her mahalleye **haftada bir gün** gidilir.
#
# Niye bir gün: minimum sepet 500 ₺, yani müşteri haftalık pazar alışverişi yapıyor.
# Haftada bir dolu sepet, haftada iki yarım sepetten hem müşteri hem rota için daha iyi.
# Komşu mahallelerde talep büyürse ikinci gün eklenir — model buna hazır, bir mahalleye
# birden fazla `HaftalikTeslimGunu` eklenebiliyor.
#
# Gün → o gün gidilen mahalleler. **Sıra kurye güzergâhıdır**: listedeki sıra
# `sira` alanına yazılıyor, yani araç yukarıdan aşağı o sırayla dolaşır.
#
# ⚠ BU GRUPLAMA TASLAKTIR. Hangi mahallenin hangisine komşu olduğunu Ersin bilir;
# panelden (Hizmet verilen mahalleler → teslim günü) ya da buradan düzeltilir.
# Değiştirdikten sonra: python manage.py ornek_veri --rotalari_esitle
GUN_ROTALARI = {
    Gun.PAZARTESI: ["icerisehir", "muftu", "hamidiye"],
    Gun.SALI:      ["bahcelievler", "esentepe"],
    Gun.CARSAMBA:  ["yeni", "beytepe"],
    Gun.PERSEMBE:  ["haciakif", "haciarmagan"],
    Gun.CUMA:      ["avsar", "evsat"],
    Gun.CUMARTESI: ["dalyan", "yesilyurt"],
}

# Mahalle kısa adı → (gün, güzergâhtaki sıra). Yukarıdaki tablodan üretiliyor;
# elle doldurmaya gerek yok.
MERKEZ_ROTALARI = {
    slug: (gun, sira)
    for gun, slugler in GUN_ROTALARI.items()
    for sira, slug in enumerate(slugler, start=1)
}

MERKEZ_KAPASITE = 40      # sipariş / gün
KIRSAL_KAPASITE = 20      # köy kökenli mahalleler açıldığında başlangıç değeri


class Command(BaseCommand):
    help = "Beyşehir mağazasını, merkez hizmet mahallelerini ve takvimi oluşturur."

    def add_arguments(self, ayristirici):
        ayristirici.add_argument(
            "--rotalari_esitle", action="store_true",
            help="Merkez mahallelerini yukarıdaki GUN_ROTALARI tablosuna göre eşitler: "
                 "tabloda olmayan teslim günlerini ve gelecekteki takvim kayıtlarını siler, "
                 "güzergâh sırasını tabloya göre düzeltir.")

    def handle(self, *args, **secenekler):
        self.esitle = secenekler["rotalari_esitle"]
        if self.esitle:
            self.stdout.write(self.style.WARNING(
                "Rota eşitleme açık: rotada olmayan teslim günleri ve onların gelecekteki "
                "takvim kayıtları silinecek."))

        # -- coğrafya hazır mı --------------------------------------------
        ilce = Ilce.objects.filter(il__ad="Konya", slug="beysehir").first()
        if ilce is None:
            self.stdout.write("Coğrafya verisi eksik, yükleniyor…")
            call_command("cografya_yukle", sessiz=True)
            ilce = Ilce.objects.filter(il__ad="Konya", slug="beysehir").first()
        if ilce is None:
            self.stdout.write(self.style.ERROR(
                "Beyşehir ilçesi bulunamadı. core/cografya_verisi.py dosyasını kontrol edin."))
            return

        # -- mağaza -------------------------------------------------------
        magaza, yeni = Magaza.objects.get_or_create(
            slug="beysehir",
            defaults={
                "ad": "Bostanhane Beyşehir",
                "il": ilce.il,
                "ilce": ilce,
                "adres": "Depo adresi girilecek",
                "telefon": "0332 000 00 00",
                "eposta": "beysehir@bostanhane.com",
            },
        )
        self.yaz(f"Mağaza: {magaza.ad} ({magaza.konum})", yeni)

        # Satış ayarları kaydı: yeni mağazada sinyal açıyor, eski mağazada
        # (bu kayıt eklenmeden önce oluşmuş olanda) burada açılıyor.
        ayarlar = SatisAyarlari.getir(magaza)
        self.stdout.write(
            f"  Satış ayarları: minimum {ayarlar.min_sepet_tutari:.0f} ₺ · "
            f"teslimat {ayarlar.teslimat_ucreti:.0f} ₺ · "
            f"ücretsiz eşiği {ayarlar.ucretsiz_teslimat_esigi:.0f} ₺ "
            f"(panelden değiştirilir)")

        # -- merkez mahalleleri: aktif, teslim günleriyle -------------------
        self.stdout.write("\nMerkez mahalleleri (aktif):")
        toplam_takvim = 0
        toplam_silinen_kural = 0
        toplam_silinen_gun = 0
        sira = 0
        for mahalle_slug, (gun, gun_ici_sira) in MERKEZ_ROTALARI.items():
            mahalle = Mahalle.objects.filter(ilce=ilce, slug=mahalle_slug).first()
            if mahalle is None:
                self.stdout.write(self.style.WARNING(
                    f"  ! {mahalle_slug} mahallesi Beyşehir listesinde yok, atlandı."))
                continue
            sira += 1

            # Sıra = gün numarası × 10 + güzergâhtaki sıra. Böylece listeler
            # pazartesiden cumartesiye, her gün içinde de güzergâh sırasına dizilir.
            hizmet, yeni = HizmetMahallesi.objects.get_or_create(
                magaza=magaza, mahalle=mahalle,
                defaults={"gunluk_kapasite": MERKEZ_KAPASITE,
                          "sira": int(gun) * 10 + gun_ici_sira, "aktif": True},
            )
            gunler = [gun]
            kural, yeni_kural = HaftalikTeslimGunu.objects.get_or_create(
                hizmet_mahallesi=hizmet,
                gun=gun,
                defaults={
                    "teslim_baslangic": time(9, 0),
                    "teslim_bitis": time(18, 0),
                    "kesim_gun_farki": 1,
                    "kesim_saati": time(18, 0),
                },
            )
            toplam_takvim += len(TeslimTakvimi.kural_uret(kural, hafta_sayisi=8))

            if self.esitle:
                # Güzergâh sırası artık anlamlı (araç yukarıdan aşağı dolaşıyor),
                # o yüzden eşitleme sırayı da tabloya göre düzeltiyor.
                hedef_sira = int(gun) * 10 + gun_ici_sira
                if hizmet.sira != hedef_sira:
                    self.stdout.write(
                        f"    ~ {mahalle.ad}: güzergâh sırası {hizmet.sira} → {hedef_sira}")
                    hizmet.sira = hedef_sira
                    hizmet.save(update_fields=["sira"])
                silinen_kural, silinen_gun = self.rotayi_esitle(hizmet, gunler)
                toplam_silinen_kural += silinen_kural
                toplam_silinen_gun += silinen_gun

            self.yaz(f"  {mahalle.ad} — {hizmet.teslim_gunleri_metni()} "
                     f"(güzergâhta {gun_ici_sira}.)", yeni)

        # -- köy kökenli mahalleler: pasif kayıt ---------------------------
        # Neden hiç eklemeyip boş bırakmıyoruz: pasif kayıt panelde listede
        # görünür, açmak için tek kutucuk yeter. Sonra tek tek aramaktan iyidir.
        kirsal = Mahalle.objects.filter(ilce=ilce, tip=Mahalle.Tip.KIRSAL).order_by("ad")
        eklenen_kirsal = 0
        for konum, mahalle in enumerate(kirsal, start=101):
            _, yeni = HizmetMahallesi.objects.get_or_create(
                magaza=magaza, mahalle=mahalle,
                defaults={"gunluk_kapasite": KIRSAL_KAPASITE, "sira": konum, "aktif": False},
            )
            eklenen_kirsal += 1 if yeni else 0
        self.stdout.write(
            f"\nKöy kökenli mahalleler: {kirsal.count()} kayıt pasif "
            f"({eklenen_kirsal} yeni). Teslim günü tanımlanmadı."
        )

        # -- özet ----------------------------------------------------------
        aktif_adet = magaza.hizmet_mahalleleri.filter(aktif=True).count()
        pasif_adet = magaza.hizmet_mahalleleri.filter(aktif=False).count()
        self.stdout.write(self.style.SUCCESS(
            f"\nTamam. Takvime {toplam_takvim} teslim günü eklendi."
        ))
        self.stdout.write(
            f"Beyşehir'de {Mahalle.objects.filter(ilce=ilce).count()} mahalle tanımlı: "
            f"{aktif_adet} aktif, {pasif_adet} pasif."
        )
        if self.esitle:
            self.stdout.write(
                f"Eşitleme: {toplam_silinen_kural} fazla teslim günü ve "
                f"{toplam_silinen_gun} takvim kaydı silindi."
            )
        self.stdout.write("Yönetim paneli: /yonetim/core/hizmetmahallesi/")

    # ----------------------------------------------------------------------
    def rotayi_esitle(self, hizmet, gunler):
        """
        Mahallenin teslim günlerini rotaya indirir: rotada olmayan
        `HaftalikTeslimGunu` kayıtlarını ve onlardan üretilmiş **gelecek**
        takvim günlerini siler.

        Neden gerekti: `get_or_create` eksik günü ekler ama fazlasını almaz.
        Rotalar değiştiğinde eski günler yenilerin üzerine birikiyordu —
        Müftü dört günlük görünüyordu.

        Yalnızca `--rotalari_esitle` ile çalışır. Varsayılan davranış
        "var olana dokunma" olarak kalıyor; panelden elle eklenen bir teslim
        günü bir komut yüzünden kaybolmasın.
        """
        silinen_kural = 0
        for kural in hizmet.haftalik_gunler.exclude(gun__in=gunler):
            self.stdout.write(self.style.WARNING(
                f"  − {hizmet.mahalle.ad}: {kural.get_gun_display()} kaldırıldı"))
            kural.delete()
            silinen_kural += 1

        # Takvim kayıtları kurala değil mahalleye bağlı; bu yüzden haftanın
        # gününe bakarak temizliyoruz. Geçmişe dokunmuyoruz: tarihçe kalsın.
        bugun = timezone.localdate()
        silinen_gun = 0
        for kayit in hizmet.takvim.filter(tarih__gt=bugun):
            if kayit.tarih.weekday() in gunler:
                continue
            if not self.takvim_silinebilir(kayit):
                self.stdout.write(self.style.WARNING(
                    f"    ! {kayit.tarih:%d.%m.%Y} siparişli, silinmedi"))
                continue
            kayit.delete()
            silinen_gun += 1

        return silinen_kural, silinen_gun

    @staticmethod
    def takvim_silinebilir(kayit):
        """
        Takvim gününe bağlı sipariş var mı? Sipariş modeli henüz yok; koşulu
        şimdiden yazıyoruz ki `siparis` uygulaması eklendiğinde bu komut
        gerçek siparişli bir günü silmeye kalkmasın.
        """
        siparisler = getattr(kayit, "siparisler", None)
        return siparisler is None or not siparisler.exists()

    def yaz(self, metin, yeni):
        if yeni:
            self.stdout.write(self.style.SUCCESS(f"+ {metin}"))
        else:
            self.stdout.write(f"· {metin} (zaten vardı)")
