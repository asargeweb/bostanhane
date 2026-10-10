"""
Bostanhane — core görünümleri (views)

Bu dosya `core/views.py` yerine geçer.

Ana sayfa: teslim günleri ve mahalleler.

**Kaldırılan:** burada bir `IlgiFormu` vardı — ziyaretçi e-postasını ve mahallesini
serbest metin olarak bırakıyordu. Yerini `/mahalleme-gelin/` sayfası aldı.

Neden kaldırıldı: eski form **ilçe sormuyordu**. İlçesiz kayıt talep haritasında
bir yere oturmuyor, "nereye talep var" sorusuna cevap vermiyordu. Yeni sayfa
il → ilçe → mahalle soruyor ve resmî mahalleye bağlıyor.

Claude Code 3 Ekim'de şablondan formu çıkardı; bu görünümdeki POST işleyicisi
kullanılmadan duruyordu. Ölü kod yanıltıcıdır: sonradan bakan "demek iki yerden
kayıt açılıyor" diye düşünür.
"""

from django.shortcuts import render

from .models import Gun, Magaza


def ana_sayfa(request):
    """Teslim günleri ve o günlere düşen mahalleler."""
    magaza = Magaza.objects.filter(aktif=True).select_related("il", "ilce").first()
    return render(request, "core/ana_sayfa.html", {
        "magaza": magaza,
        "gunler": gun_gun_mahalleler(magaza),
    })


def gun_gun_mahalleler(magaza):
    """
    Teslim takvimini **gün başlıklı** döndürür:

        [{"ad": "Pazartesi", "mahalleler": [İçerişehir, Müftü, Hamidiye]}, …]

    Ziyaretçinin sorusu "benim günüm hangisi" değil, "bugün nereye gidiyorsunuz".
    Mahalle listesinin yanına gün yazmak yerine günü başlık yapmak bu soruyu
    doğrudan cevaplıyor — ve haftanın tamamı tek bakışta görünüyor.

    Mahalleler `sira` alanına göre dizili geliyor: sıra kurye güzergâhı
    (bkz. ornek_veri.GUN_ROTALARI).
    """
    if magaza is None:
        return []

    hizmetler = (magaza.hizmet_mahalleleri
                 .filter(aktif=True)
                 .select_related("mahalle")
                 .prefetch_related("haftalik_gunler"))

    kova = {}
    for hizmet in hizmetler:
        for kural in hizmet.haftalik_gunler.all():
            if kural.aktif:
                kova.setdefault(kural.gun, []).append(hizmet)

    return [
        {"deger": deger, "ad": ad, "mahalleler": kova[deger]}
        for deger, ad in Gun.choices
        if deger in kova
    ]
