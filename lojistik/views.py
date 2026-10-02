"""
Kurye ekranları (Adım 6b): bugünün teslimatları, güzergâh sırasıyla rota, teslim kaydı.

Kapıda ödeme yok — kart önceden çekiliyor. Tutar yalnızca müşteri sorarsa
söylensin diye görünür.

Hangi kuryenin hangi rotayı gördüğü `TeslimTakvimi.kuryenin_rotalari`'nda:
atanmış rota yalnızca kuryesine, atanmamış rota mağazanın bütün kuryelerine
görünür. Bu dosyada ayrıca kural yazılmıyor.
"""

from django.contrib import messages
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from core.models import TeslimTakvimi
from hesaplar.erisim import personel_gerekli
from hesaplar.models import Rol
from siparis.models import Siparis

KURYE_ROLLERI = {Rol.KURYE, Rol.MAGAZA_YONETICISI}
kurye_gerekli = personel_gerekli(KURYE_ROLLERI, "Kurye ekranı")

# Kuryenin işi bu iki durumda: paketlendi (yola çıkmayı bekliyor) ya da yolda.
# KESILDI olan henüz toplanmadı, kuryeye gösterilmez.
TESLIM_EDILECEK = [Siparis.Durum.HAZIRLANIYOR, Siparis.Durum.YOLDA]
ULASILAMADI = "ulaşılamadı"


def gorulebilen_rotalar(request):
    """Bu kişinin görebileceği rotalar: kendi mağazası + atama kuralı."""
    sorgu = TeslimTakvimi.objects.filter(hizmet_mahallesi__magaza=request.magaza)
    return TeslimTakvimi.kuryenin_rotalari(request.user, sorgu)


@kurye_gerekli
def bugun(request):
    """Bugünün teslimatları, mahalle başına kaç paket — güzergâh sırasıyla."""
    takvimler = (gorulebilen_rotalar(request)
                 .filter(tarih=timezone.localdate())
                 .select_related("hizmet_mahallesi__mahalle", "kurye")
                 .annotate(
                     bekleyen=Count("siparisler", filter=Q(siparisler__durum__in=TESLIM_EDILECEK)),
                     teslim=Count("siparisler", filter=Q(siparisler__durum=Siparis.Durum.TESLIM_EDILDI)),
                     toplanmadi=Count("siparisler", filter=Q(siparisler__durum__in=[
                         Siparis.Durum.ALINDI, Siparis.Durum.KESILDI])))
                 .filter(Q(bekleyen__gt=0) | Q(teslim__gt=0) | Q(toplanmadi__gt=0))
                 .order_by("hizmet_mahallesi__sira"))
    return render(request, "kurye/bugun.html", {"takvimler": takvimler,
                                                "bugun": timezone.localdate()})


def _rota_siparisleri(takvim):
    return (takvim.siparisler
            .filter(durum__in=TESLIM_EDILECEK + [Siparis.Durum.TESLIM_EDILDI])
            .annotate(paket=Count("kalemler", filter=~Q(kalemler__teslim_miktari=0)))
            .order_by("olusturuldu"))


@kurye_gerekli
def rota(request, pk):
    takvim = get_object_or_404(
        gorulebilen_rotalar(request).select_related("hizmet_mahallesi__mahalle", "kurye"), pk=pk)
    siparisler = list(_rota_siparisleri(takvim))
    for siparis in siparisler:
        siparis.ulasilamadi = ULASILAMADI in siparis.ic_not
    # Teslim edilenler sona: kuryenin gözü sıradaki kapıda olsun.
    siparisler.sort(key=lambda s: s.durum == Siparis.Durum.TESLIM_EDILDI)
    return render(request, "kurye/rota.html", {
        "takvim": takvim,
        "siparisler": siparisler,
        "yola_cikacak": sum(1 for s in siparisler if s.durum == Siparis.Durum.HAZIRLANIYOR),
    })


@kurye_gerekli
@require_POST
def yola_cik(request, pk):
    """Paketlenmiş siparişleri YOLDA yapar — müşteri "Yolda" görsün. Paneldeki işlemle aynı."""
    takvim = get_object_or_404(gorulebilen_rotalar(request), pk=pk)
    adet = takvim.siparisler.filter(durum=Siparis.Durum.HAZIRLANIYOR).update(
        durum=Siparis.Durum.YOLDA, guncellendi=timezone.now())
    messages.success(request, f"{adet} sipariş yola çıktı.")
    return redirect("kurye_rota", pk=pk)


def _kuryenin_siparisi(request, numara):
    """Başka kuryeye atanmış rotanın siparişi açılmaz — adres ve telefon kişisel veri."""
    return get_object_or_404(
        Siparis.objects.select_related("teslim_takvimi__hizmet_mahallesi__mahalle"),
        numara=numara, magaza=request.magaza, teslim_takvimi__in=gorulebilen_rotalar(request))


@kurye_gerekli
def teslim(request, numara):
    siparis = _kuryenin_siparisi(request, numara)
    if siparis.teslim_enlem is not None and siparis.teslim_boylam is not None:
        harita = f"{siparis.teslim_enlem},{siparis.teslim_boylam}"
    else:
        harita = (f"{siparis.teslim_acik_adres}, {siparis.teslim_mahalle} Mahallesi, "
                  f"{siparis.teslim_ilce}, {siparis.teslim_il}")
    notlar = [satir for satir in siparis.ic_not.splitlines() if ULASILAMADI in satir]
    return render(request, "kurye/teslim.html", {
        "siparis": siparis,
        "harita": harita,
        "ulasilamadi_notlari": notlar,
        "teslim_edilebilir": siparis.durum in TESLIM_EDILECEK,
        "eksikler": siparis.eksik_kalemler,
    })


@kurye_gerekli
@require_POST
def teslim_et(request, numara):
    siparis = _kuryenin_siparisi(request, numara)
    if siparis.durum not in TESLIM_EDILECEK:
        messages.error(request, f"Bu sipariş teslime açık değil ({siparis.get_durum_display()}).")
        return redirect("kurye_teslim", numara=numara)
    # Durum ve teslim zamanı birlikte modelde ayarlanıyor; otomatik onay süresi buna bağlı.
    siparis.teslim_edildi_isaretle()
    messages.success(request, f"{siparis.teslim_ad_soyad} — teslim edildi.")
    return redirect("kurye_rota", pk=siparis.teslim_takvimi_id) if siparis.teslim_takvimi_id \
        else redirect("kurye")


@kurye_gerekli
@require_POST
def ulasilamadi(request, numara):
    """
    Kapıda kimse yok: sipariş YOLDA kalır, iç nota saat yazılır. Yeni durum yok —
    iade / yeniden deneme akışına henüz karar verilmedi. Sipariş listeden düşmez.
    """
    siparis = _kuryenin_siparisi(request, numara)
    if siparis.durum not in TESLIM_EDILECEK:
        messages.error(request, "Bu sipariş teslime açık değil.")
        return redirect("kurye_teslim", numara=numara)
    saat = timezone.localtime().strftime("%d.%m %H.%M")
    siparis.durum = Siparis.Durum.YOLDA
    siparis.ic_not = f"{siparis.ic_not}\n{saat} — {ULASILAMADI} (kurye: {request.user.ad_soyad})".strip()
    siparis.save(update_fields=["durum", "ic_not", "guncellendi"])
    messages.info(request, f"{siparis.teslim_ad_soyad}: ulaşılamadı olarak not düşüldü. "
                           f"Sipariş listede kalıyor.")
    return redirect("kurye_rota", pk=siparis.teslim_takvimi_id) if siparis.teslim_takvimi_id \
        else redirect("kurye")
