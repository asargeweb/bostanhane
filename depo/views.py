"""
Paketleme ekranları (Adım 6a): teslim günleri, günün siparişleri, toplama ve tartım.

Tablette parmakla kullanılır: büyük düğme, büyük yazı, az seçenek.
Tartım hesabı modelde (`SiparisKalemi.tartim_gir`); burada yalnızca çağrılıyor.

Alım listesi ayrı dosyada: `depo/alim.py` (Cowork).
"""

from datetime import timedelta
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from core.araclar import para_yaz
from core.models import TeslimTakvimi
from hesaplar.erisim import personel_gerekli
from hesaplar.models import Rol
from odeme.islemler import cekim_yap
from siparis.models import Siparis, SiparisKalemi, gunu_kes

DEPO_ROLLERI = {Rol.PAKETLEME, Rol.MAGAZA_YONETICISI}

# Toplama açıkken sipariş bu durumlardan birinde olmalı.
TOPLANABILIR = {Siparis.Durum.KESILDI, Siparis.Durum.HAZIRLANIYOR}


# Paketleme elemanı, mağaza yöneticisi ve süper admin girer; personel yalnızca kendi
# mağazasını görür. (Alım listesi ekranı da bu adla kullanıyor.)
depo_gerekli = personel_gerekli(DEPO_ROLLERI, "Depo ekranı")


def _miktar(metin):
    try:
        return Decimal(str(metin).replace(",", ".").strip())
    except (InvalidOperation, TypeError):
        return None


def erken_kesebilir_mi(kullanici):
    """Kesim saatinden önce kesmek yönetici kararı (kapasite doldu gibi); paketleme bekler."""
    return kullanici.super_admin_mi or kullanici.rol == Rol.MAGAZA_YONETICISI


@depo_gerekli
def gunler(request):
    """
    Bugünün ve yarının teslim günleri (yarının günü bugün 18.00'de kesilir), ayrıca
    önümüzdeki iki haftada siparişi olan günler — Cumartesi alınan Pazartesi
    siparişi depoda önceden görünsün.
    """
    bugun = timezone.localdate()
    takvimler = (TeslimTakvimi.objects
                 .filter(hizmet_mahallesi__magaza=request.magaza,
                         tarih__range=(bugun, bugun + timedelta(days=14)))
                 .exclude(durum=TeslimTakvimi.Durum.IPTAL)
                 .select_related("hizmet_mahallesi__mahalle")
                 .annotate(
                     siparis_adet=Count("siparisler", filter=~Q(siparisler__durum=Siparis.Durum.IPTAL)),
                     hazir_adet=Count("siparisler", filter=Q(siparisler__durum__in=[
                         Siparis.Durum.HAZIRLANIYOR, Siparis.Durum.YOLDA, Siparis.Durum.TESLIM_EDILDI])))
                 .order_by("tarih", "hizmet_mahallesi__sira"))
    yarin = bugun + timedelta(days=1)
    gruplar = {}
    for takvim in takvimler:
        if takvim.tarih > yarin and not takvim.siparis_adet:
            continue
        gruplar.setdefault(takvim.tarih, []).append(takvim)
    # Kesim saati geçmiş ama kesilmemiş günler — tarihi ne olursa olsun. Zamanlanmış
    # `gunu_kes` kurulana kadar insan gözü yedek: kesilmeyen günde sipariş akmaya
    # devam eder, alım listesi kesinleşmez.
    kesilmemis = list(TeslimTakvimi.objects
                      .filter(hizmet_mahallesi__magaza=request.magaza,
                              durum=TeslimTakvimi.Durum.ACIK, kesim_zamani__lte=timezone.now())
                      .select_related("hizmet_mahallesi__mahalle")
                      .order_by("kesim_zamani"))
    return render(request, "depo/gunler.html", {
        "gruplar": sorted(gruplar.items()),
        "bugun": bugun,
        "yarin": yarin,
        "simdi": timezone.now(),
        "kesilmemis": kesilmemis,
    })


@depo_gerekli
def gun(request, pk):
    takvim = get_object_or_404(
        TeslimTakvimi.objects.select_related("hizmet_mahallesi__mahalle"),
        pk=pk, hizmet_mahallesi__magaza=request.magaza)
    siparisler = (takvim.siparisler.exclude(durum=Siparis.Durum.IPTAL)
                  .select_related("uye")
                  .annotate(kalem_adet=Count("kalemler"),
                            tartilan=Count("kalemler", filter=Q(kalemler__teslim_miktari__isnull=False)))
                  .order_by("olusturuldu"))
    kesim_gecti = timezone.now() >= takvim.kesim_zamani
    return render(request, "depo/gun.html", {
        "takvim": takvim,
        "siparisler": siparisler,
        "kesildi": takvim.durum != TeslimTakvimi.Durum.ACIK,
        "kesebilir": takvim.durum == TeslimTakvimi.Durum.ACIK
                     and (kesim_gecti or erken_kesebilir_mi(request.user)),
        "kesim_gecti": kesim_gecti,
    })


@depo_gerekli
@require_POST
def gunu_kes_view(request, pk):
    takvim = get_object_or_404(TeslimTakvimi, pk=pk, hizmet_mahallesi__magaza=request.magaza)
    if timezone.now() < takvim.kesim_zamani and not erken_kesebilir_mi(request.user):
        messages.error(request, "Kesim saati gelmedi; sipariş hâlâ değişebilir.")
        return redirect("depo_gun", pk=pk)
    try:
        adet = gunu_kes(takvim)
    except ValidationError as hata:
        messages.error(request, " ".join(hata.messages))
    else:
        messages.success(request, f"Gün kesildi: {adet} sipariş toplamaya açıldı.")
    return redirect("depo_gun", pk=pk)


def _toplanacak_siparis(request, numara):
    return get_object_or_404(
        Siparis.objects.select_related("teslim_takvimi__hizmet_mahallesi__mahalle"),
        numara=numara, magaza=request.magaza)


@depo_gerekli
def toplama(request, numara):
    siparis = _toplanacak_siparis(request, numara)
    # Kesilmemiş günde toplama açılmaz: müşteri kesime kadar siparişi değiştirebilir,
    # yarım toplanmış sipariş değişirse tartım boşa gider.
    if siparis.durum == Siparis.Durum.ALINDI:
        messages.error(request, "Bu günün kesimi yapılmadı; sipariş hâlâ değişebilir. "
                                "Toplama kesimden sonra açılır.")
        return redirect("depo_gun", pk=siparis.teslim_takvimi_id) if siparis.teslim_takvimi_id \
            else redirect("depo")
    kalemler = list(siparis.kalemler.select_related("magaza_urun__urun__birim"))
    return render(request, "depo/toplama.html", {
        "siparis": siparis,
        "kalemler": kalemler,
        "duzenlenebilir": siparis.durum in TOPLANABILIR,
        "kalan": sum(1 for k in kalemler if k.teslim_miktari is None),
    })


@depo_gerekli
@require_POST
def tartim(request, numara, pk):
    siparis = _toplanacak_siparis(request, numara)
    if siparis.durum not in TOPLANABILIR:
        messages.error(request, "Bu sipariş toplamaya açık değil.")
        return redirect("depo_toplama", numara=numara)
    kalem = get_object_or_404(SiparisKalemi.objects.select_related("magaza_urun__urun__birim"),
                              pk=pk, siparis=siparis)
    if "bulunamadi" in request.POST:
        miktar = Decimal("0")
    else:
        miktar = _miktar(request.POST.get("miktar"))
        if miktar is None or miktar < 0:
            messages.error(request, f"{kalem.urun_adi}: miktarı sayı olarak yazın.")
            return redirect("depo_toplama", numara=numara)
        if not kalem.magaza_urun.urun.birim.kesirli and miktar % 1:
            messages.error(request, f"{kalem.urun_adi}: {kalem.birim_adi} kesirli olamaz.")
            return redirect("depo_toplama", numara=numara)
    try:
        kalem.tartim_gir(miktar, kullanici=request.user)
    except ValidationError as hata:
        messages.error(request, " ".join(hata.messages))
    return redirect(f"{reverse('depo_toplama', args=[numara])}#k{kalem.pk}")


@depo_gerekli
@require_POST
def hazir(request, numara):
    siparis = _toplanacak_siparis(request, numara)
    if siparis.durum != Siparis.Durum.KESILDI:
        messages.error(request, "Bu sipariş zaten hazır ya da toplamaya açık değil.")
        return redirect("depo_toplama", numara=numara)
    if siparis.kalemler.filter(teslim_miktari__isnull=True).exists():
        messages.error(request, "Tartılmamış ürün var. Hepsini tartın ya da \"bulunamadı\" deyin.")
        return redirect("depo_toplama", numara=numara)
    # Paneldeki "hazırlandı" işlemiyle aynı iki alan.
    siparis.durum = Siparis.Durum.HAZIRLANIYOR
    siparis.hazirlandi_zamani = timezone.now()
    siparis.save(update_fields=["durum", "hazirlandi_zamani", "guncellendi"])
    messages.success(request, f"{siparis.numara} hazır. Kesin tutar: {para_yaz(siparis.toplam)}")

    # Kesin tutarı karttan çek. Başarısızsa hazır durumu geri alınmaz — mal hazır,
    # para sorunu ayrı bir iş; yöneticinin görmesi için not düşülür.
    try:
        cekim = cekim_yap(siparis, kullanici=request.user)
        sorun = "" if cekim.basarili_mi else (cekim.hata_mesaji or "banka onay vermedi")
    except ValidationError as hata:
        sorun = " ".join(hata.messages)
    if sorun:
        saat = timezone.localtime().strftime("%d.%m %H.%M")
        siparis.ic_not = f"{siparis.ic_not}\n{saat} — çekim yapılamadı: {sorun}".strip()
        siparis.save(update_fields=["ic_not", "guncellendi"])
        messages.warning(request, f"Para çekilemedi: {sorun} Yöneticiye haber verin.")
    else:
        messages.info(request, f"Karttan {para_yaz(cekim.tutar)} çekildi.")
    return redirect("depo_gun", pk=siparis.teslim_takvimi_id) if siparis.teslim_takvimi_id \
        else redirect("depo")
