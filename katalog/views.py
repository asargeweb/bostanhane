"""
Vitrin: kategori sayfası ve ürün sayfası.

Satışta olan ürün `MagazaUrun.satista_mi` ile anlaşılır; o özellik fiyatı, satışta
kutucuğunu, durumu ve stoğu birlikte denetliyor. Burada ayrı bir koşul yazılmıyor.

Tükenen ya da mevsimi geçen ürün listeden düşmez, soluk görünür: müşteri
"bu hafta yok" ile "artık satmıyorlar" arasındaki farkı görmeli.
"""

from decimal import Decimal

from django.db.models import Q
from django.shortcuts import get_object_or_404, render

from siparis.vitrin_araclari import vitrin_gerekli

from .models import Kategori, MagazaUrun

# Görsel yüklenene kadar kartta kategoriye göre bir simge duruyor.
KATEGORI_SIMGELERI = {
    "sebze": "🥬", "yesillik": "🌿", "meyve": "🍎", "yumurta": "🥚",
    "bakliyat-ve-kuru-gida": "🫘", "yoresel-urun": "🍯",
}


def vitrindeki_kayitlar(magaza):
    """
    Vitrinde görünecek mağaza ürünleri: fiyatı girilmiş ve ya satışta ya da
    bilerek "tükendi / mevsim dışı" işaretlenmiş olanlar. Fiyatı hiç girilmemiş,
    satışa hiç açılmamış ürün müşteriye gösterilmez.
    """
    return (MagazaUrun.objects
            .filter(magaza=magaza, fiyat__isnull=False, urun__aktif=True,
                    urun__kategori__aktif=True)
            .filter(Q(aktif=True) | ~Q(durum=MagazaUrun.Durum.SATISTA))
            .select_related("urun__kategori", "urun__birim"))


def kart_bilgisi(kayit):
    """Kartta gösterilecek durum: satışta mı, değilse ne yazılsın."""
    urun = kayit.urun
    adim = urun.satis_adimi
    # Başlangıç miktarı: adım 1'den küçükse 1 kg (domates 500 g adımla, 1 kg'dan başlar).
    baslangic = adim if adim >= 1 else max(adim, Decimal("1"))
    if kayit.satista_mi:
        etiket, not_metni = None, None
    elif kayit.durum == MagazaUrun.Durum.MEVSIM_DISI:
        etiket = "Mevsim dışı"
        not_metni = f"Mevsimi: {urun.mevsim}" if urun.mevsim else "Mevsimi gelince dönecek"
    else:
        etiket, not_metni = "Tükendi", "Bu hafta bulunamadı"
    return {
        "kayit": kayit,
        "urun": urun,
        "satista": kayit.satista_mi,
        "etiket": etiket,
        "not_metni": not_metni,
        "simge": KATEGORI_SIMGELERI.get(urun.kategori.slug, "🧺"),
        "baslangic": baslangic,
    }


@vitrin_gerekli
def vitrin(request, kategori=None):
    kayitlar = vitrindeki_kayitlar(request.magaza)
    kargo = request.GET.get("kanal") == "kargo"

    # Ray sayıları seçili kategoriden bağımsız: müşteri her başlıkta kaç ürün olduğunu görsün.
    sayilar = {}
    for kategori_id in kayitlar.values_list("urun__kategori_id", flat=True):
        sayilar[kategori_id] = sayilar.get(kategori_id, 0) + 1
    kategoriler = [(k, sayilar[k.pk]) for k in Kategori.objects.filter(aktif=True)
                   if k.pk in sayilar]
    kargo_sayisi = kayitlar.filter(urun__kargo_satis=True).count()

    secili = None
    if kategori:
        secili = get_object_or_404(Kategori, slug=kategori, aktif=True)
        kayitlar = kayitlar.filter(urun__kategori=secili)
    if kargo:
        kayitlar = kayitlar.filter(urun__kargo_satis=True)

    kartlar = [kart_bilgisi(k) for k in kayitlar.order_by(
        "urun__kategori__sira", "urun__sira", "urun__ad")]
    # Satışta olanlar önde, soluk olanlar sonda.
    kartlar.sort(key=lambda k: not k["satista"])

    return render(request, "katalog/vitrin.html", {
        "kartlar": kartlar,
        "kategoriler": kategoriler,
        "secili": secili,
        "kargo": kargo,
        "kargo_sayisi": kargo_sayisi,
        "toplam": sum(sayilar.values()),
    })


@vitrin_gerekli
def urun(request, slug):
    kayit = get_object_or_404(vitrindeki_kayitlar(request.magaza), urun__slug=slug)
    kart = kart_bilgisi(kayit)
    ayarlar = request.satis_ayarlari
    tahmini = kayit.tutar(kart["baslangic"])
    # "Tartı biraz eksik çıkarsa" örneği: somut bir sayı, soyut açıklamadan iyi anlatıyor.
    ornek_tarti = (kart["baslangic"] * Decimal("0.95")).quantize(Decimal("0.001"))
    return render(request, "katalog/urun.html", {
        **kart,
        "tampon": ayarlar.provizyon_tampon_orani,
        "tahmini": tahmini,
        "bloke": ayarlar.provizyon_tutari(tahmini) if kayit.urun.tartili_mi else tahmini,
        "ornek_tarti": ornek_tarti,
        "ornek_tutar": kayit.tutar(ornek_tarti),
    })
