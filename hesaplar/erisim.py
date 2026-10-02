"""
Personel ekranlarının (depo, kurye) giriş kapısı.

Paketleme elemanı ve kurye yönetim paneline girmez; kendi sade ekranlarını
kullanır. Kural her ekranda aynı: belli roller girer, personel yalnızca kendi
mağazasını görür, süper admin `?magaza=` ile mağaza seçer.
"""

from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

from core.models import Magaza


def personel_gerekli(roller, ekran_adi):
    """
    `roller` dışındaki herkesi ana sayfaya gönderir. Geçenlere `request.magaza`
    verilir; sorgular buna göre süzülmeli (mağaza izolasyonu sorgu seviyesinde).
    """
    def bezeyici(gorunum):
        @wraps(gorunum)
        @login_required
        def sarmal(request, *args, **kwargs):
            kullanici = request.user
            if kullanici.super_admin_mi:
                magazalar = Magaza.objects.filter(aktif=True).order_by("pk")
                secilen = request.GET.get("magaza") or request.session.get("personel_magaza")
                magaza = (magazalar.filter(pk=secilen).first()
                          if str(secilen or "").isdigit() else None) or magazalar.first()
                if magaza:
                    request.session["personel_magaza"] = magaza.pk
            elif kullanici.rol in roller:
                magaza = kullanici.magaza
            else:
                messages.error(request, f"{ekran_adi} yalnızca mağaza personeli içindir.")
                return redirect("ana_sayfa")
            if magaza is None:
                messages.error(request, "Hesabınız bir mağazaya bağlı değil.")
                return redirect("ana_sayfa")
            request.magaza = magaza
            return gorunum(request, *args, **kwargs)
        return sarmal
    return bezeyici
