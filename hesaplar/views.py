"""
Üyelik ekranları: kayıt, giriş, çıkış, hesabım, adreslerim, siparişlerim.

Şifre sıfırlama ve SMS doğrulaması yok: SMS sağlayıcısı seçilmedi. Sağlayıcı
gelince kayıt sonrasına bir kod ekranı girecek.
"""

from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from core.models import Ilce, Mahalle
from siparis.models import Siparis
from siparis.vitrin_araclari import ziyaretci_sepetini_kat

from .forms import AdresFormu, GirisFormu, HesapFormu, KayitFormu
from .models import Adres


def _sonraki(request, varsayilan="hesabim"):
    """Girişten sonra gidilecek yer. Başka siteye yönlendirme açığı olmasın."""
    hedef = request.POST.get("next") or request.GET.get("next")
    if hedef and url_has_allowed_host_and_scheme(hedef, {request.get_host()},
                                                 require_https=request.is_secure()):
        return hedef
    return varsayilan


def kayit(request):
    if request.user.is_authenticated:
        return redirect("hesabim")
    form = KayitFormu(request.POST or None)
    if request.method == "POST" and form.is_valid():
        kullanici = form.kaydet()
        eski_anahtar = request.session.session_key
        login(request, kullanici, backend="django.contrib.auth.backends.ModelBackend")
        ziyaretci_sepetini_kat(request, eski_anahtar)
        messages.success(request, f"Hoş geldiniz, {kullanici.get_short_name()}! "
                                  f"Teslim gününüzü görmek için bir adres ekleyin.")
        return redirect(_sonraki(request, "adres_ekle"))
    return render(request, "hesaplar/kayit.html", {"form": form, "next": _sonraki(request, "")})


def giris(request):
    if request.user.is_authenticated:
        return redirect(_sonraki(request))
    form = GirisFormu(request, request.POST or None)
    if request.method == "POST" and form.is_valid():
        # Django girişte oturum anahtarını değiştirir; ziyaretçi sepetini bulmak
        # için eski anahtarı önceden alıyoruz.
        eski_anahtar = request.session.session_key
        login(request, form.kullanici)
        ziyaretci_sepetini_kat(request, eski_anahtar)
        return redirect(_sonraki(request, "vitrin"))
    return render(request, "hesaplar/giris.html", {"form": form, "next": _sonraki(request, "")})


@require_POST
def cikis(request):
    logout(request)
    messages.info(request, "Çıkış yaptınız.")
    return redirect("ana_sayfa")


@login_required
def hesabim(request):
    form = HesapFormu(request.POST if "bilgiler" in request.POST else None,
                      instance=request.user)
    sifre_formu = PasswordChangeForm(request.user,
                                     request.POST if "sifre" in request.POST else None)
    if request.method == "POST":
        if "bilgiler" in request.POST and form.is_valid():
            form.save()
            messages.success(request, "Bilgileriniz kaydedildi.")
            return redirect("hesabim")
        if "sifre" in request.POST and sifre_formu.is_valid():
            sifre_formu.save()
            update_session_auth_hash(request, sifre_formu.user)  # oturum kapanmasın
            messages.success(request, "Şifreniz değiştirildi.")
            return redirect("hesabim")

    adres = request.user.varsayilan_adres
    return render(request, "hesaplar/hesabim.html", {
        "form": form,
        "sifre_formu": sifre_formu,
        "adres": adres,
        "hizmet": adres.hizmet_mahallesi if adres else None,
        "adres_sayisi": request.user.adresler.filter(aktif=True).count(),
        "son_siparis": request.user.siparisler.first(),
    })


# -- adresler --------------------------------------------------------------
@login_required
def adresler(request):
    kayitlar = (request.user.adresler.filter(aktif=True)
                .select_related("mahalle__ilce__il"))
    return render(request, "hesaplar/adresler.html", {"adresler": kayitlar})


@login_required
def adres_formu(request, pk=None):
    adres = get_object_or_404(Adres, pk=pk, uye=request.user, aktif=True) if pk else None
    form = AdresFormu(request.POST or None, instance=adres, uye=request.user)
    if request.method == "POST" and form.is_valid():
        kayit = form.save()
        if kayit.yerel_teslimat_var:
            messages.success(request, f"Adres kaydedildi. {kayit.mahalle.ad} Mahallesi "
                                      f"teslim günü: {kayit.hizmet_mahallesi.teslim_gunleri_metni()}.")
        else:
            messages.warning(request, "Adres kaydedildi. Bu mahalleye kurye gitmiyor; "
                                      "kargo ile gönderim açıldığında bu adresi kullanabilirsiniz.")
        return redirect(_sonraki(request, "adresler"))
    return render(request, "hesaplar/adres_form.html", {"form": form, "adres": adres})


@login_required
@require_POST
def adres_varsayilan(request, pk):
    adres = get_object_or_404(Adres, pk=pk, uye=request.user, aktif=True)
    adres.varsayilan = True
    adres.save()
    messages.success(request, f"“{adres.baslik}” varsayılan adresiniz oldu.")
    return redirect("adresler")


@login_required
@require_POST
def adres_sil(request, pk):
    """
    Adres silinmez, kapatılır: geçmiş siparişler adresin kopyasını taşıyor ama
    sepet ve raporlar kayda bağlı kalabilir. Başlık serbest kalsın diye yeniden adlandırılır
    (üye + başlık veritabanında tekil).
    """
    adres = get_object_or_404(Adres, pk=pk, uye=request.user, aktif=True)
    varsayilandi = adres.varsayilan
    adres.aktif = False
    adres.varsayilan = False
    adres.baslik = f"{adres.baslik[:24]} · silindi {adres.pk}"
    adres.save()
    if varsayilandi:
        sonraki = request.user.adresler.filter(aktif=True).first()
        if sonraki:
            sonraki.varsayilan = True
            sonraki.save()
    messages.info(request, "Adres silindi.")
    return redirect("adresler")


def ilceler(request):
    """Adres formu için: seçilen ilin ilçeleri."""
    il = request.GET.get("il", "")
    kayitlar = Ilce.objects.filter(il_id=il).values("pk", "ad") if il.isdigit() else []
    return JsonResponse({"secenekler": list(kayitlar)})


def mahalleler(request):
    """Adres formu için: seçilen ilçenin mahalleleri."""
    ilce = request.GET.get("ilce", "")
    kayitlar = Mahalle.objects.filter(ilce_id=ilce).values("pk", "ad") if ilce.isdigit() else []
    return JsonResponse({"secenekler": list(kayitlar)})


def mahalle_bilgi(request, pk):
    """
    Mahalle seçilince bilgi kutusu: kurye gidiyor mu, hangi gün.
    Müşteri bunu adresi kaydetmeden, formda öğrensin — sipariş sonunda değil.
    """
    mahalle = get_object_or_404(Mahalle, pk=pk)
    hizmet = mahalle.yerel_hizmet()
    if hizmet is None:
        return JsonResponse({"yerel": False, "mahalle": mahalle.ad})
    kural = hizmet.haftalik_gunler.filter(aktif=True).first()
    kesim = ""
    if kural:
        once = "bir gün" if kural.kesim_gun_farki == 1 else f"{kural.kesim_gun_farki} gün"
        kesim = f"{once} önce {kural.kesim_saati:%H.%M}"
    return JsonResponse({"yerel": True, "mahalle": mahalle.ad,
                         "gunler": hizmet.teslim_gunleri_metni(), "kesim": kesim})


# -- siparişler ------------------------------------------------------------
@login_required
def siparislerim(request):
    kayitlar = (request.user.siparisler
                .select_related("teslim_takvimi")
                .prefetch_related("kalemler"))
    return render(request, "hesaplar/siparisler.html", {"siparisler": kayitlar})


@login_required
def siparis_detay(request, numara):
    siparis = get_object_or_404(
        Siparis.objects.select_related("teslim_takvimi").prefetch_related("kalemler"),
        numara=numara, uye=request.user)
    return render(request, "hesaplar/siparis_detay.html", {"siparis": siparis})


@login_required
@require_POST
def siparis_iptal(request, numara):
    siparis = get_object_or_404(Siparis, numara=numara, uye=request.user)
    try:
        siparis.iptal_et(kullanici=request.user, sebep="Müşteri iptal etti")
    except ValidationError as hata:
        messages.error(request, " ".join(hata.messages))
    else:
        messages.success(request, f"{siparis.numara} numaralı sipariş iptal edildi.")
    return redirect("siparis_detay", numara=numara)

