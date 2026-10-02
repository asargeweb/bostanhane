"""
Bostanhane — alım listesi ekranı

Bu dosya `depo/alim.py` olarak kaydedilir. `depo/views.py`'ye dokunmuyor;
CC'nin paketleme görünümleriyle çakışmasın diye ayrı dosyada.

**Bu ekran işin kalbi.** "Önce talep, sonra alım" burada somutlaşıyor: mağaza
sabah hale bu listeyle gidiyor, listede olmayanı almıyor, fazlasını almıyor.

### Neden gün, neden mahalle değil

Talimatta `/depo/alim/<takvim>/` yazmıştım — yanlıştı. `TeslimTakvimi` bir
mahallenin bir günü. Ama hale **günde bir kez** gidiliyor; o gün üç mahalleye
teslimat varsa üçünün talebi tek sepette toplanmalı. Üç ayrı liste, üç ayrı
hal yolculuğu demek olurdu.

Bu yüzden adres tarihe bağlı: `/depo/alim/2026-10-05/`. `alim_listesi()`
işlevi de zaten tarih alıyor, mahalle değil.

### Neden saklanmıyor

Liste her açılışta siparişlerden yeniden hesaplanıyor. Bir sipariş iptal
edilirse liste kendiliğinden doğru kalıyor. Saklasaydık güncel tutmak ayrı bir
iş olurdu ve bir gün kaçırırdık.
"""

from collections import OrderedDict
from datetime import date, timedelta
from decimal import Decimal

from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from core.araclar import para_yaz
from core.models import TeslimTakvimi
from katalog.models import MagazaUrun
from siparis.models import Siparis, alim_listesi

from .views import depo_gerekli


def _tarih_coz(metin):
    """'2026-10-05' → date. Bozuk tarihte 404; kullanıcı adresi elle yazmış olabilir."""
    try:
        return date.fromisoformat(str(metin))
    except (TypeError, ValueError):
        raise Http404("Tarih anlaşılmadı.")


def _miktar_yaz(sayi, birim_adi):
    """
    12.500 → '12,5 kg'. Sondaki sıfırlar atılır, ondalık virgülle yazılır.

    Hale giden kişi için kilogramı grama çevirmiyoruz: tezgâhta konuşulan
    birim kilogram. Müşteri ekranında 500 g yazmak doğru, burada değil.
    """
    sayi = Decimal(str(sayi or 0)).normalize()
    if sayi == sayi.to_integral_value():
        metin = f"{sayi.to_integral_value():,}".replace(",", ".")
    else:
        metin = f"{sayi:,.3f}".replace(",", "#").replace(".", ",").replace("#", ".")
        metin = metin.rstrip("0").rstrip(",")
    return f"{metin} {birim_adi}"


@depo_gerekli
def alim(request, tarih):
    """
    Bir günün alım listesi: o gün hangi üründen kaç birim alınacak.

    Kategoriye göre gruplanıyor — haldeki yürüyüş sırası bu: sebze reyonu,
    yeşillik, meyve. Alfabetik tek liste mağazayı hal içinde ileri geri
    yürütürdü.
    """
    gun = _tarih_coz(tarih)
    magaza = request.magaza

    takvimler = list(TeslimTakvimi.objects
                     .filter(hizmet_mahallesi__magaza=magaza, tarih=gun)
                     .exclude(durum=TeslimTakvimi.Durum.IPTAL)
                     .select_related("hizmet_mahallesi__mahalle")
                     .order_by("hizmet_mahallesi__sira"))
    if not takvimler:
        raise Http404("Bu tarihte teslimat yok.")

    satirlar = alim_listesi(magaza, gun)

    # Kategori ve tartılı bilgisi `alim_listesi`'nde yok (o sorgu sipariş
    # satırlarından geliyor, ürün tanımından değil). Tek sorguyla tamamlıyoruz.
    urunler = {
        mu.pk: mu for mu in MagazaUrun.objects
        .filter(pk__in=[s["magaza_urun"] for s in satirlar])
        .select_related("urun__kategori", "urun__birim")
    }

    gruplar = OrderedDict()
    genel_toplam = Decimal("0.00")
    tartili_var = False
    for satir in satirlar:
        magaza_urun = urunler.get(satir["magaza_urun"])
        urun = magaza_urun.urun if magaza_urun else None
        kategori = urun.kategori.ad if urun and urun.kategori_id else "Diğer"
        tartili = bool(urun and urun.tartili_mi)
        tartili_var = tartili_var or tartili
        tutar = satir["tahmini_tutar"] or Decimal("0.00")
        genel_toplam += tutar
        gruplar.setdefault(kategori, []).append({
            "ad": satir["urun_adi"],
            "miktar": _miktar_yaz(satir["toplam_miktar"], satir["birim_adi"]),
            "siparis_sayisi": satir["siparis_sayisi"],
            "tutar": para_yaz(tutar),
            "tartili": tartili,
            "anahtar": satir["magaza_urun"],
            "uyari": getattr(urun, "uyari_metni", "") if urun else "",
        })

    # Kesilmemiş gün varsa liste kesin değil: müşteri hâlâ ürün ekleyebilir.
    kesilmemis = [t for t in takvimler if t.durum == TeslimTakvimi.Durum.ACIK]
    siparis_adedi = (Siparis.objects
                     .filter(magaza=magaza, teslim_takvimi__tarih=gun, test_siparisi=False)
                     .exclude(durum=Siparis.Durum.IPTAL).count())
    deneme_adedi = (Siparis.objects
                    .filter(magaza=magaza, teslim_takvimi__tarih=gun, test_siparisi=True)
                    .exclude(durum=Siparis.Durum.IPTAL).count())

    return render(request, "depo/alim.html", {
        "gun": gun,
        "onceki": gun - timedelta(days=1),
        "sonraki": gun + timedelta(days=1),
        "takvimler": takvimler,
        "gruplar": gruplar.items(),
        "kalem_sayisi": len(satirlar),
        "genel_toplam": para_yaz(genel_toplam),
        "siparis_adedi": siparis_adedi,
        "deneme_adedi": deneme_adedi,
        "kesilmemis": kesilmemis,
        "en_erken_kesim": min((t.kesim_zamani for t in kesilmemis), default=None),
        "tartili_var": tartili_var,
        "simdi": timezone.now(),
    })


@depo_gerekli
def alim_takvimden(request, pk):
    """
    `/depo/alim/takvim/<pk>/` → o takvimin tarihine yönlendirir.

    Gün sayfasından gelen bağlantı elinde takvim tutuyor; tarihi oradan
    çıkarmak yerine burada çeviriyoruz ki şablon basit kalsın.
    """
    takvim = get_object_or_404(TeslimTakvimi, pk=pk,
                              hizmet_mahallesi__magaza=request.magaza)
    return redirect("depo_alim", tarih=takvim.tarih.isoformat())
