"""
Sepet ekranı.

Ödeme yok (sanal POS seçilmedi). Vitrin TEST modundayken sepet "deneme siparişi"
olarak siparişe çevrilebilir: sipariş akışını, panel ekranlarını ve alım listesini
gerçek veriyle denemek için. AÇIK modda POS gelene kadar sipariş düğmesi kapalı.

Sepet ve sipariş kuralları modelde (`siparise_hazir_mi`, `siparise_cevir`); burada
yalnızca çağrılıyorlar.
"""

from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from katalog.models import MagazaUrun

from .models import SepetKalemi
from .vitrin_araclari import sepet_bul, siradaki_teslimler, vitrin_gerekli


def _miktar(metin):
    try:
        return Decimal(str(metin).replace(",", "."))
    except (InvalidOperation, TypeError):
        return None


def _geri(request, varsayilan="sepet"):
    hedef = request.POST.get("next") or request.META.get("HTTP_REFERER")
    if hedef and url_has_allowed_host_and_scheme(hedef, {request.get_host()},
                                                 require_https=request.is_secure()):
        return hedef
    return varsayilan


@vitrin_gerekli
def sepet(request):
    sepet = sepet_bul(request, request.magaza)
    adresler = []
    gunler = []
    if request.user.is_authenticated:
        adresler = list(request.user.adresler.filter(aktif=True)
                        .select_related("mahalle__ilce__il"))
        # Adres seçilmemişse varsayılan adres öne gelsin; müşteri her seferinde seçmesin.
        if sepet and sepet.adres_id is None and request.user.varsayilan_adres:
            sepet.adres = request.user.varsayilan_adres
            sepet.save(update_fields=["adres", "guncellendi"])
    if sepet and sepet.adres_id:
        gunler = siradaki_teslimler(sepet.adres.hizmet_mahallesi)
        # Seçili gün artık geçerli değilse (kesim geçti) ilk açık gün seçilsin.
        if gunler and (sepet.teslim_takvimi_id is None
                       or sepet.teslim_takvimi_id not in {g.pk for g in gunler}):
            sepet.teslim_takvimi = gunler[0]
            sepet.save(update_fields=["teslim_takvimi", "guncellendi"])

    kalemler = (sepet.kalemler.select_related("magaza_urun__urun__birim")
                if sepet else [])
    hazir, sebep = sepet.siparise_hazir_mi() if sepet else (False, "Sepetiniz boş.")
    return render(request, "siparis/sepet.html", {
        "sepet": sepet,
        "kalemler": kalemler,
        "adresler": adresler,
        "gunler": gunler,
        "hazir": hazir,
        "sebep": sebep,
        "ayarlar": request.satis_ayarlari,
    })


@vitrin_gerekli
@require_POST
def sepete_ekle(request, pk):
    kayit = get_object_or_404(MagazaUrun.objects.select_related("urun__birim"),
                              pk=pk, magaza=request.magaza)
    miktar = _miktar(request.POST.get("miktar")) or kayit.urun.satis_adimi
    sepet = sepet_bul(request, request.magaza, olustur=True)
    try:
        sepet.ekle(kayit, miktar)
    except ValidationError as hata:
        messages.error(request, " ".join(hata.messages))
    else:
        messages.success(request, f"{kayit.urun.ad} sepete eklendi.")
    return redirect(_geri(request, "vitrin"))


@vitrin_gerekli
@require_POST
def kalem_guncelle(request, pk):
    sepet = sepet_bul(request, request.magaza)
    kalem = get_object_or_404(SepetKalemi, pk=pk, sepet=sepet)
    miktar = _miktar(request.POST.get("miktar"))
    if "sil" in request.POST or (miktar is not None and miktar <= 0):
        kalem.delete()
        messages.info(request, f"{kalem.urun.ad} sepetten çıkarıldı.")
        return redirect("sepet")
    if miktar is not None:
        kalem.miktar = miktar
        try:
            kalem.full_clean()
        except ValidationError as hata:
            messages.error(request, " ".join(hata.messages))
        else:
            kalem.save()
    return redirect("sepet")


@vitrin_gerekli
@login_required
@require_POST
def teslimat_sec(request):
    """Sepette adres ve teslim günü seçimi."""
    sepet = sepet_bul(request, request.magaza, olustur=True)
    adres = request.user.adresler.filter(pk=request.POST.get("adres") or 0, aktif=True).first()
    if adres and adres.pk != sepet.adres_id:
        sepet.adres = adres
        sepet.teslim_takvimi = None          # gün mahalleye bağlı; adres değişince yeniden seçilir
    gun = request.POST.get("gun")
    if gun and sepet.adres_id:
        gecerli = {g.pk: g for g in siradaki_teslimler(sepet.adres.hizmet_mahallesi)}
        if gun.isdigit() and int(gun) in gecerli:
            sepet.teslim_takvimi = gecerli[int(gun)]
    sepet.save(update_fields=["adres", "teslim_takvimi", "guncellendi"])
    return redirect("sepet")


@vitrin_gerekli
@login_required
@require_POST
def siparis_ver(request):
    if not request.satis_ayarlari.test_modunda_mi:
        messages.error(request, "Ödeme sistemi henüz açılmadı; sipariş alınamıyor.")
        return redirect("sepet")
    sepet = sepet_bul(request, request.magaza)
    if sepet is None:
        return redirect("sepet")
    try:
        siparis = sepet.siparise_cevir(kullanici=request.user)
    except ValidationError as hata:
        messages.error(request, " ".join(hata.messages))
        return redirect("sepet")
    messages.success(request, f"Deneme siparişiniz alındı: {siparis.numara}. "
                              f"Gerçek değildir, ödeme alınmadı.")
    return redirect("siparis_detay", numara=siparis.numara)

