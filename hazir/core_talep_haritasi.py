"""
Bostanhane — talep haritası

Bu dosya `core/talep_haritasi.py` olarak kaydedilir ve `core/admin.py` içindeki
`IlgiKaydiAdmin` tarafından kullanılır.

### Ne işe yarıyor

"Nereye şube açalım?" sorusunun cevabı. Tek tek ilgi kayıtlarına bakmak bu
soruyu cevaplamıyor; **toplamak** gerekiyor:

    Üzümlü · Beyşehir / Konya   4.855 kişi   37 talep   %0,8   hizmet yok
    Adaköy · Beyşehir / Konya     319 kişi    2 talep   %0,6   hizmet yok

Nüfusu yan yana koymanın sebebi: 37 talep tek başına bir şey söylemiyor.
10.000 kişilik mahalleden gelen 37 talep zayıf, 400 kişilik mahalleden gelen
37 talep güçlü sinyaldir. Oran olmadan büyük mahalleler hep önde görünür ve
yanlış yere şube açılır.

### Neden ayrı bir sayfa

Django'nun liste ekranı satır satır gösteriyor; gruplama yapmıyor. Bu yüzden
panele küçük bir sayfa ekliyoruz: `/yonetim/core/ilgikaydi/harita/`.
"""

from django.db.models import Count, Q

from .models import HizmetMahallesi, Ilce, IlgiKaydi, Mahalle


def talep_haritasi(ilce=None, en_az=1):
    """
    İlçe ve mahalle bazında talep sayıları.

    Dönen satırlar talep sayısına göre sıralı. Resmî mahalleye bağlanabilmiş
    kayıtlar mahalle bazında, bağlanamayanlar ("yazdığı mahalle listede yok")
    ilçe altında ayrı bir satırda toplanıyor — kaybolmasınlar.
    """
    kayitlar = IlgiKaydi.objects.all()
    if ilce is not None:
        kayitlar = kayitlar.filter(ilce=ilce)

    # 1) Resmî mahalleye bağlı olanlar
    mahalle_sayilari = (kayitlar.filter(mahalle__isnull=False)
                        .values("mahalle")
                        .annotate(adet=Count("pk"),
                                  haber_verilen=Count("pk", filter=Q(haber_verildi=True)))
                        .order_by())
    mahalle_idleri = [s["mahalle"] for s in mahalle_sayilari]
    mahalleler = {
        m.pk: m for m in Mahalle.objects.filter(pk__in=mahalle_idleri)
        .select_related("ilce__il")
    }
    hizmet_verilen = set(
        HizmetMahallesi.objects.filter(mahalle_id__in=mahalle_idleri, aktif=True)
        .values_list("mahalle_id", flat=True))

    satirlar = []
    for sayi in mahalle_sayilari:
        mahalle = mahalleler.get(sayi["mahalle"])
        if mahalle is None:
            continue
        nufus = mahalle.nufus
        satirlar.append({
            "mahalle": mahalle,
            "ad": mahalle.ad,
            "ilce": mahalle.ilce,
            "adet": sayi["adet"],
            "haber_verilen": sayi["haber_verilen"],
            "nufus": nufus,
            "nufus_yazi": f"{nufus:,}".replace(",", ".") if nufus else None,
            "nufus_yili": mahalle.nufus_yili,
            # Binde olarak: küçük sayılarda yüzde hep "0" görünüyor.
            "binde": (sayi["adet"] * 1000 / nufus) if nufus else None,
            "hizmet_var": mahalle.pk in hizmet_verilen,
            "bagli": True,
        })

    # 2) Mahallesi eşleşmemiş olanlar — ilçe altında tek satır
    eslesmeyen = (kayitlar.filter(mahalle__isnull=True, ilce__isnull=False)
                  .values("ilce")
                  .annotate(adet=Count("pk"),
                            haber_verilen=Count("pk", filter=Q(haber_verildi=True)))
                  .order_by())
    ilceler = {i.pk: i for i in Ilce.objects
               .filter(pk__in=[s["ilce"] for s in eslesmeyen]).select_related("il")}
    for sayi in eslesmeyen:
        ilce_nesne = ilceler.get(sayi["ilce"])
        if ilce_nesne is None:
            continue
        satirlar.append({
            "mahalle": None,
            "ad": "— mahallesi eşleşmeyenler —",
            "ilce": ilce_nesne,
            "adet": sayi["adet"],
            "haber_verilen": sayi["haber_verilen"],
            "nufus": None,
            "nufus_yazi": None,
            "nufus_yili": None,
            "binde": None,
            "hizmet_var": False,
            "bagli": False,
        })

    # 3) Ne ilçesi ne mahallesi belli olanlar (eski "yakında" formu kayıtları)
    yersiz = kayitlar.filter(mahalle__isnull=True, ilce__isnull=True).count()

    satirlar = [s for s in satirlar if s["adet"] >= en_az]
    satirlar.sort(key=lambda s: (-s["adet"], s["ad"]))
    return satirlar, yersiz


# "En güçlü sinyal" için en küçük nüfus. 24 kişilik bir mahalleden gelen
# 3 talep binde 125 çıkıyor ve bütün listeyi eziyor — oysa oraya şube açmak
# anlamsız. Küçük sayılarda oran gürültüye dönüşüyor; eşik onu susturuyor.
EN_KUCUK_NUFUS = 200


def ozet(satirlar):
    """Sayfanın üstündeki dört rakam."""
    hizmetsiz = [s for s in satirlar if not s["hizmet_var"]]
    adaylar = [s for s in hizmetsiz
               if s["binde"] is not None and (s["nufus"] or 0) >= EN_KUCUK_NUFUS]
    return {
        "toplam_talep": sum(s["adet"] for s in satirlar),
        "yer_sayisi": len(satirlar),
        "hizmetsiz_talep": sum(s["adet"] for s in hizmetsiz),
        "en_guclu": max(adaylar, key=lambda s: s["binde"], default=None),
        "en_kucuk_nufus": EN_KUCUK_NUFUS,
    }
