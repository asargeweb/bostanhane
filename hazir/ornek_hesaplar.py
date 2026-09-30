"""
Bostanhane — örnek hesaplar komutu

Dosya yolu: hesaplar/management/commands/ornek_hesaplar.py
Çalıştırma:  python manage.py ornek_hesaplar

Beyşehir mağazası için birer mağaza yöneticisi, paketleme elemanı ve kurye,
ayrıca adresi olan iki örnek üye oluşturur. Panelde rollerin ve adres
yapısının nasıl göründüğünü görmek için.

GÜVENLİK: Bu hesaplar **şifresiz** oluşturulur, yani hiçbiri giriş yapamaz.
Şifreyi yönetim panelinden siz verirsiniz. Böylece komut canlı sunucuda
çalışsa bile bilinen şifreli bir kapı açılmaz.

Tekrar çalıştırılabilir; var olan kayıtları bozmaz.
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from core.models import Magaza, Mahalle
from hesaplar.models import Adres, Kullanici, Rol


PERSONEL = [
    # (telefon, ad soyad, rol)
    ("5320000001", "Mehmet Yönetici", Rol.MAGAZA_YONETICISI),
    ("5320000002", "Ayşe Paketleme", Rol.PAKETLEME),
    ("5320000003", "Hasan Kurye", Rol.KURYE),
]

UYELER = [
    # (telefon, ad soyad, mahalle slug, adres, bina/kat/daire, kuryeye not)
    ("5321110001", "Fatma Demir", "yeni",
     "Atatürk Caddesi, Zeytin Apartmanı", ("12", "3", "7"), "Zil çalışmıyor, arayın."),
    ("5321110002", "Ali Kaya", "muftu",
     "Gölkenarı Sokak, Çınar Sitesi B Blok", ("4", "1", "2"), "Site girişinde güvenliğe bırakılabilir."),
]


class Command(BaseCommand):
    help = "Beyşehir mağazası için örnek personel ve üye hesapları oluşturur."

    @transaction.atomic
    def handle(self, *args, **secenekler):
        magaza = Magaza.objects.filter(slug="beysehir").first()
        if magaza is None:
            self.stdout.write(self.style.ERROR(
                "Beyşehir mağazası bulunamadı. Önce şunu çalıştırın: python manage.py ornek_veri"
            ))
            return

        for telefon, ad_soyad, rol in PERSONEL:
            kullanici, yeni = Kullanici.objects.get_or_create(
                telefon=telefon,
                defaults={"ad_soyad": ad_soyad, "rol": rol, "magaza": magaza},
            )
            if yeni:
                kullanici.set_unusable_password()
                kullanici.save()
            self.yaz(f"{kullanici.get_rol_display()}: {ad_soyad}", yeni)

        for telefon, ad_soyad, mahalle_slug, acik_adres, bkd, tarif in UYELER:
            mahalle = Mahalle.objects.filter(ilce=magaza.ilce, slug=mahalle_slug).first()
            if mahalle is None:
                self.stdout.write(self.style.WARNING(f"  ! {mahalle_slug} mahallesi yok, atlandı."))
                continue

            uye, yeni = Kullanici.objects.get_or_create(
                telefon=telefon,
                defaults={"ad_soyad": ad_soyad, "rol": Rol.UYE},
            )
            if yeni:
                uye.set_unusable_password()
                uye.save()
            self.yaz(f"Üye: {ad_soyad}", yeni)

            bina_no, kat, daire = bkd
            adres, yeni_adres = Adres.objects.get_or_create(
                uye=uye,
                baslik="Ev",
                defaults={
                    "mahalle": mahalle,
                    "acik_adres": acik_adres,
                    "bina_no": bina_no,
                    "kat": kat,
                    "daire": daire,
                    "tarif": tarif,
                    "varsayilan": True,
                },
            )
            self.yaz(f"  Adres: {adres.baslik} — {mahalle.ad}", yeni_adres)

        self.stdout.write(self.style.SUCCESS(
            "\nTamam. Hesaplar şifresiz oluşturuldu; giriş yapabilmeleri için "
            "yönetim panelinden şifre vermeniz gerekir."
        ))
        self.stdout.write("Yönetim paneli: /yonetim/hesaplar/kullanici/")

    def yaz(self, metin, yeni):
        if yeni:
            self.stdout.write(self.style.SUCCESS(f"+ {metin}"))
        else:
            self.stdout.write(f"· {metin} (zaten vardı)")
