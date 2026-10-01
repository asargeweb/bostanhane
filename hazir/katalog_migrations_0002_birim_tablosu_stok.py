"""
Birim sabit listeden tabloya geçer; mağaza ürününe stok ve stok defteri eklenir.

Elle yazıldı: Django kendi başına `birim` metin alanını silip yabancı anahtar
olarak yeniden kurardı ve var olan ürünlerin birimi kaybolurdu. Burada önce
tablo açılıyor, eski değerler taşınıyor, eski sütun ancak ondan sonra kalkıyor.
"""

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

# Eski sabit liste: (değer, ad, kesirli mi)
ILK_BIRIMLER = [
    ("kg", "Kilogram", True),
    ("adet", "Adet", False),
    ("demet", "Demet", False),
    ("paket", "Paket", False),
    ("kavanoz", "Kavanoz", False),
    ("sise", "Şişe", False),
    ("kutu", "Kutu", False),
]
# Kısa yazılış ekranda görünür; "sise" yerine "şişe" yazılsın.
KISALTMA = {"sise": "şişe"}


def birimleri_tasi(apps, schema_editor):
    Birim = apps.get_model("katalog", "Birim")
    Urun = apps.get_model("katalog", "Urun")
    eslesme = {}
    for sira, (deger, ad, kesirli) in enumerate(ILK_BIRIMLER, start=1):
        birim, _ = Birim.objects.get_or_create(
            kisaltma=KISALTMA.get(deger, deger),
            defaults={"ad": ad, "kesirli": kesirli, "sira": sira})
        eslesme[deger] = birim
    for urun in Urun.objects.all():
        urun.birim_yeni = eslesme.get(urun.birim) or eslesme["adet"]
        urun.save(update_fields=["birim_yeni"])


def birimleri_geri_al(apps, schema_editor):
    Urun = apps.get_model("katalog", "Urun")
    geri = {KISALTMA.get(d, d): d for d, _, _ in ILK_BIRIMLER}
    for urun in Urun.objects.select_related("birim_yeni"):
        urun.birim = geri.get(urun.birim_yeni.kisaltma, "adet") if urun.birim_yeni else "kg"
        urun.save(update_fields=["birim"])


class Migration(migrations.Migration):

    dependencies = [
        ("katalog", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # -- birim tablosu ---------------------------------------------------
        migrations.CreateModel(
            name="Birim",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("olusturuldu", models.DateTimeField(auto_now_add=True, verbose_name="oluşturulma")),
                ("guncellendi", models.DateTimeField(auto_now=True, verbose_name="güncellenme")),
                ("ad", models.CharField(help_text="Örnek: Kilogram, Demet, Kavanoz.", max_length=40, unique=True, verbose_name="birim adı")),
                ("kisaltma", models.CharField(help_text="Listede ve fiyatın yanında görünür. Örnek: kg, demet.", max_length=12, unique=True, verbose_name="kısa yazılış")),
                ("kesirli", models.BooleanField(default=False, help_text="İşaretliyse 0,5 gibi kesirli miktarla satılır (kilogram gibi). Tartılı ürün yalnızca kesirli birimle satılabilir.", verbose_name="kesirli satılır")),
                ("sira", models.PositiveIntegerField(default=0, verbose_name="sıra")),
                ("aktif", models.BooleanField(default=True, help_text="Kapalıysa yeni üründe seçilemez; eski ürünler etkilenmez.", verbose_name="aktif")),
            ],
            options={
                "verbose_name": "birim",
                "verbose_name_plural": "birimler",
                "ordering": ["sira", "ad"],
            },
        ),
        migrations.AddField(
            model_name="urun",
            name="birim_yeni",
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name="+", to="katalog.birim"),
        ),
        migrations.RunPython(birimleri_tasi, birimleri_geri_al),
        migrations.RemoveField(model_name="urun", name="birim"),
        migrations.RenameField(model_name="urun", old_name="birim_yeni", new_name="birim"),
        migrations.AlterField(
            model_name="urun",
            name="birim",
            field=models.ForeignKey(limit_choices_to={"aktif": True}, on_delete=django.db.models.deletion.PROTECT, related_name="urunler", to="katalog.birim", verbose_name="birim"),
        ),

        # -- stok ------------------------------------------------------------
        migrations.AddField(
            model_name="magazaurun",
            name="stok",
            field=models.DecimalField(blank=True, decimal_places=3, help_text="Boşsa stok takip edilmez (sınırsız). Yalnızca stok hareketiyle değişir: Ürünler listesindeki “ekle / çıkar” ile.", max_digits=10, null=True, verbose_name="stok"),
        ),
        migrations.CreateModel(
            name="StokHareketi",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("olusturuldu", models.DateTimeField(auto_now_add=True, verbose_name="oluşturulma")),
                ("guncellendi", models.DateTimeField(auto_now=True, verbose_name="güncellenme")),
                ("tur", models.CharField(choices=[("mal_kabul", "Mal kabul"), ("fire", "Fire"), ("sayim", "Sayım düzeltmesi"), ("satis", "Satış"), ("iade", "İade"), ("takip_kapatildi", "Takip kapatıldı")], max_length=16, verbose_name="tür")),
                ("miktar", models.DecimalField(decimal_places=3, help_text="Giriş artı, çıkış eksi.", max_digits=10, verbose_name="miktar")),
                ("onceki_stok", models.DecimalField(blank=True, decimal_places=3, max_digits=10, null=True, verbose_name="önceki stok")),
                ("sonraki_stok", models.DecimalField(blank=True, decimal_places=3, max_digits=10, null=True, verbose_name="sonraki stok")),
                ("aciklama", models.CharField(blank=True, max_length=200, verbose_name="açıklama")),
                ("kullanici", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="+", to=settings.AUTH_USER_MODEL, verbose_name="kim")),
                ("magaza_urun", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="stok_hareketleri", to="katalog.magazaurun", verbose_name="mağaza ürünü")),
            ],
            options={
                "verbose_name": "stok hareketi",
                "verbose_name_plural": "stok hareketleri",
                "ordering": ["-olusturuldu", "-pk"],
            },
        ),
    ]
