"""
Bostanhane — ürün listesini Excel'den içeri alır

Dosya yolu: katalog/management/commands/urun_yukle.py
Çalıştırma:  python manage.py urun_yukle
             python manage.py urun_yukle --dosya "C:\\yol\\urunler.xlsx"

Dosya şu sırayla aranır:
  1. `veri/urunler.xlsx`        → **repoda duran tohum dosyası**, sunucuya da gider
  2. `..\\icerik\\urunler.xlsx` → Ersin'in üzerinde çalıştığı dosya (repoda değil)

İkisi arasındaki fark önemli: `icerik\\` Ersin'in çalışma dosyası, `veri\\` ise canlıya
giden kopya. Listeyi güncellediğinizde `veri\\urunler.xlsx`'i yenileyip push edin.

Beklenen sütunlar (4. satır başlık, 5. satır örnek, veri 6. satırdan başlar):
    Kategori · Ürün adı · Birim · Tartılı mı · Satış adımı ·
    Tahmini fiyat (₺ / birim) · Yerel · Kargo · Kurumsal · Raf ömrü · Mevsim · Not

Tekrar çalıştırılabilir. Var olan ürünü **günceller**, panelden girdiğiniz fiyatı
silmez: fiyat yalnızca Excel'de bir değer varsa yazılır. Böylece fiyatları panelden
girip Excel'den ürün eklemeye devam edebilirsiniz.

"ÖRNEK" ile başlayan satırlar atlanır.
"""

import re
from decimal import Decimal, InvalidOperation
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from core.araclar import turkce_slug
from core.models import Magaza
from katalog.models import Birim, Kategori, MagazaUrun, Urun

BASLIK_SATIRI = 4
VERI_BASLANGICI = 6

# Excel'de birimin farklı yazılışları → panelde tanımlı kısa yazılış
BIRIM_ESLEME = {"kilogram": "kg", "kilo": "kg", "sise": "şişe"}


def birim_bul(metin):
    """
    Birimi paneldeki Birimler tablosundan bulur (ada ya da kısa yazılışa göre).
    Tabloda olmayan birim sessizce "adet" sayılmasın diye None döner; satır hata verir.
    """
    metin = str(metin or "").strip().lower()
    metin = BIRIM_ESLEME.get(metin, metin) or "adet"
    for birim in Birim.objects.all():
        if metin in (birim.kisaltma.lower(), birim.ad.lower()):
            return birim
    return None

EVET = {"evet", "e", "yes", "true", "1", "var"}


def evet_mi(deger):
    return str(deger or "").strip().lower() in EVET


def sayi(deger):
    """'64,90' ve '64.90' ikisini de okur. Boşsa None."""
    if deger in (None, ""):
        return None
    if isinstance(deger, (int, float, Decimal)):
        return Decimal(str(deger))
    metin = str(deger).strip().replace("₺", "").replace(" ", "").replace(",", ".")
    try:
        return Decimal(metin)
    except InvalidOperation:
        return None


def satis_adimi_coz(metin, birim):
    """
    '500 g' → 0.500   ·   '1 kg' → 1   ·   '1 adet' → 1   ·   '250 g' → 0.250

    Kilogramla satılan üründe adım kilogram cinsine çevrilir; gram yazılması
    kullanıcı için daha doğal olduğu için Excel'de gram kabul ediyoruz.
    """
    if not metin:
        return Decimal("1")
    m = str(metin).strip().lower().replace(",", ".")
    rakam = re.search(r"[\d.]+", m)
    if not rakam:
        return Decimal("1")
    try:
        deger = Decimal(rakam.group())
    except InvalidOperation:
        return Decimal("1")
    if birim.kilogram_mi and re.search(r"\bg\b|gr\b|gram", m) and "kg" not in m:
        return (deger / Decimal("1000")).quantize(Decimal("0.001"))
    return deger


def raf_omru_coz(metin):
    """'5 gün' → 5 · '24 saat' → 1 · '12 ay' → 360 · '2 yıl' → 720. Boşsa None."""
    if not metin:
        return None
    m = str(metin).strip().lower()
    rakam = re.search(r"\d+", m)
    if not rakam:
        return None
    deger = int(rakam.group())
    if "saat" in m:
        return max(1, deger // 24)
    if "ay" in m:
        return deger * 30
    if "yıl" in m or "yil" in m:
        return deger * 360
    if "hafta" in m:
        return deger * 7
    return deger


class Command(BaseCommand):
    help = "icerik/urunler.xlsx dosyasındaki ürün listesini katalog'a aktarır."

    def add_arguments(self, ayristirici):
        ayristirici.add_argument("--dosya", default=None, help="Excel dosyasının yolu.")
        ayristirici.add_argument(
            "--magaza", default="beysehir",
            help="Fiyatların yazılacağı mağazanın kısa adı. Varsayılan: beysehir")
        ayristirici.add_argument(
            "--kuru_prova", action="store_true",
            help="Hiçbir şey kaydetmeden ne olacağını yazar.")
        ayristirici.add_argument(
            "--fiyatlari_guncelle", action="store_true",
            help="Panelde fiyatı girilmiş ürünlerin fiyatını da Excel'deki değerle "
                 "değiştirir. Varsayılan olarak girilmiş fiyatlara DOKUNULMAZ.")

    def handle(self, *args, **secenekler):
        try:
            from openpyxl import load_workbook
        except ImportError:
            self.stdout.write(self.style.ERROR(
                "openpyxl kurulu değil. Şunu çalıştırın: pip install openpyxl"))
            return

        if secenekler["dosya"]:
            yol = Path(secenekler["dosya"])
        else:
            adaylar = [
                Path(settings.BASE_DIR) / "veri" / "urunler.xlsx",
                Path(settings.BASE_DIR).parent / "icerik" / "urunler.xlsx",
            ]
            yol = next((a for a in adaylar if a.exists()), adaylar[0])
        if not yol.exists():
            self.stdout.write(self.style.ERROR(f"Dosya bulunamadı: {yol}"))
            self.stdout.write("Aranan yerler: veri/urunler.xlsx ve ../icerik/urunler.xlsx")
            self.stdout.write("--dosya ile yolu verebilirsiniz.")
            return

        magaza = Magaza.objects.filter(slug=secenekler["magaza"]).first()
        if magaza is None:
            self.stdout.write(self.style.ERROR(
                f"'{secenekler['magaza']}' mağazası yok. Önce: python manage.py ornek_veri"))
            return

        self.kuru = secenekler["kuru_prova"]
        self.fiyatlari_guncelle = secenekler["fiyatlari_guncelle"]
        if self.kuru:
            self.stdout.write(self.style.WARNING("KURU PROVA — hiçbir şey kaydedilmeyecek.\n"))
        if self.fiyatlari_guncelle:
            self.stdout.write(self.style.WARNING(
                "Fiyat güncelleme açık: panelde girilmiş fiyatlar Excel'deki değerle "
                "değiştirilecek.\n"))

        self.stdout.write(f"Dosya: {yol}")
        self.stdout.write(f"Mağaza: {magaza.ad}\n")

        kitap = load_workbook(yol, data_only=True)
        sayfa = kitap["Ürünler"] if "Ürünler" in kitap.sheetnames else kitap.active

        sayac = {"kategori": 0, "urun_yeni": 0, "urun_guncel": 0,
                 "fiyat": 0, "fiyat_korundu": 0, "atlanan": 0, "hata": 0}

        with transaction.atomic():
            for satir in sayfa.iter_rows(min_row=VERI_BASLANGICI, values_only=True):
                if not satir or not satir[1]:
                    continue
                urun_adi = str(satir[1]).strip()
                if urun_adi.upper().startswith("ÖRNEK"):
                    sayac["atlanan"] += 1
                    continue
                try:
                    self.satir_isle(satir, magaza, sayac)
                except Exception as hata:          # noqa: BLE001
                    sayac["hata"] += 1
                    self.stdout.write(self.style.ERROR(f"  ! {urun_adi}: {hata}"))

            if self.kuru:
                transaction.set_rollback(True)

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(
            f"{sayac['urun_yeni']} yeni ürün, {sayac['urun_guncel']} güncellenen, "
            f"{sayac['kategori']} yeni kategori, {sayac['fiyat']} fiyat yazıldı."))
        if sayac["fiyat_korundu"]:
            self.stdout.write(self.style.WARNING(
                f"{sayac['fiyat_korundu']} üründe paneldeki fiyat korundu, Excel'deki "
                f"farklı değer yazılmadı. Excel'i geçerli saymak istiyorsanız: "
                f"--fiyatlari_guncelle"))
        if sayac["atlanan"]:
            self.stdout.write(f"{sayac['atlanan']} örnek satır atlandı.")
        if sayac["hata"]:
            self.stdout.write(self.style.ERROR(f"{sayac['hata']} satır hata verdi (yukarıda)."))

        fiyatsiz = MagazaUrun.objects.filter(magaza=magaza, fiyat__isnull=True).count()
        if fiyatsiz:
            self.stdout.write(self.style.WARNING(
                f"\n{fiyatsiz} ürünün fiyatı yok, bu yüzden satışa açılmadı.\n"
                f"Fiyatları panelden girebilirsiniz: /yonetim/katalog/magazaurun/\n"
                f"Fiyat sütununu doldurup satışta kutucuğunu işaretleyin, bir kez kaydedin."))

    # ----------------------------------------------------------------------
    def satir_isle(self, satir, magaza, sayac):
        (kategori_adi, urun_adi, birim_metni, tartili, adim_metni, fiyat_degeri,
         yerel, kargo, kurumsal, raf_metni, mevsim, notu) = (list(satir) + [None] * 12)[:12]

        kategori_adi = str(kategori_adi or "Diğer").strip()
        urun_adi = str(urun_adi).strip()
        birim = birim_bul(birim_metni)
        if birim is None:
            raise ValueError(f"“{birim_metni}” birimi tanımlı değil. Panelde "
                             f"KATALOG → Birimler'den ekleyin.")
        tartili_mi = evet_mi(tartili)

        kategori, yeni_kat = Kategori.objects.get_or_create(
            slug=turkce_slug(kategori_adi),
            defaults={"ad": kategori_adi, "sira": sayac["kategori"] + 1},
        )
        sayac["kategori"] += 1 if yeni_kat else 0

        alanlar = {
            "kategori": kategori,
            "ad": urun_adi,
            "birim": birim,
            "tartili_mi": tartili_mi,
            "satis_adimi": satis_adimi_coz(adim_metni, birim),
            "yerel_satis": evet_mi(yerel),
            "kargo_satis": evet_mi(kargo),
            "kurumsal_satis": evet_mi(kurumsal),
            "raf_omru_gun": raf_omru_coz(raf_metni),
            "mevsim": str(mevsim or "").strip()[:60],
            "aciklama": str(notu or "").strip(),
            "sira": sayac["urun_yeni"] + sayac["urun_guncel"] + 1,
        }

        urun, yeni = Urun.objects.update_or_create(
            slug=turkce_slug(urun_adi), defaults=alanlar)
        # İş kuralları (kargo şartları) burada da denetlenir; Excel'deki yanlış
        # bir "evet" sessizce geçmesin.
        urun.full_clean(exclude=["slug", "gorsel"])
        urun.save()
        sayac["urun_yeni" if yeni else "urun_guncel"] += 1

        magaza_urun, _ = MagazaUrun.objects.get_or_create(magaza=magaza, urun=urun)
        fiyat = sayi(fiyat_degeri)
        korundu = False
        if fiyat is not None and fiyat > 0:
            # Panelde girilmiş fiyatın üzerine yazma. Fiyat canlıda panelden
            # yönetiliyor; Excel eskimiş olabilir ve sessizce fiyat düşürmek
            # gerçek paraya dokunur.
            if magaza_urun.fiyat is not None and not self.fiyatlari_guncelle:
                korundu = magaza_urun.fiyat != fiyat
            else:
                magaza_urun.fiyat = fiyat
                magaza_urun.aktif = True
                magaza_urun.save()
                sayac["fiyat"] += 1

        isaret = "+" if yeni else "·"
        kanal = urun.kanallar_metni
        if korundu:
            sayac["fiyat_korundu"] += 1
            fiyat_metni = (f"paneldeki {magaza_urun.fiyat} ₺ korundu "
                           f"(Excel: {fiyat} ₺)")
        elif magaza_urun.fiyat is not None:
            fiyat_metni = f"{magaza_urun.fiyat} ₺"
        else:
            fiyat_metni = "fiyat yok"
        self.stdout.write(f"{isaret} {urun_adi} ({kategori.ad}) — "
                          f"{urun.satis_adimi_metni} · {kanal} · {fiyat_metni}")
