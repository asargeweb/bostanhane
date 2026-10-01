"""
Bostanhane — core görünümleri (views)

Bu dosya `core/views.py` yerine geçer.

Şimdilik tek sayfa var: yayına hazırlık sayfası. Ziyaretçi mahallesini ve e-postasını
bırakabiliyor; bu kayıtlar yönetim panelinde "İlgi kayıtları" altında birikiyor.
Açılışta ilk haber verilecek kitle bu liste olacak.
"""

from django import forms
from django.contrib import messages
from django.shortcuts import redirect, render

from .models import Gun, IlgiKaydi, Magaza


class IlgiFormu(forms.ModelForm):
    class Meta:
        model = IlgiKaydi
        fields = ["eposta", "telefon", "mahalle_adi"]
        widgets = {
            "eposta": forms.EmailInput(attrs={
                "placeholder": "e-posta adresiniz", "required": True, "autocomplete": "email"}),
            "telefon": forms.TextInput(attrs={
                "placeholder": "telefon (isteğe bağlı)", "autocomplete": "tel"}),
            "mahalle_adi": forms.TextInput(attrs={
                "placeholder": "mahalleniz", "autocomplete": "off"}),
        }


def ana_sayfa(request):
    """Yayına hazırlık sayfası ve ilgi kaydı formu."""
    if request.method == "POST":
        form = IlgiFormu(request.POST)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                "Kaydınızı aldık. Mahallenize başladığımız gün ilk siz haberdar olacaksınız."
            )
            return redirect("ana_sayfa")
    else:
        form = IlgiFormu()

    magaza = Magaza.objects.filter(aktif=True).select_related("il", "ilce").first()
    gunler = gun_gun_mahalleler(magaza)

    return render(request, "core/ana_sayfa.html", {
        "form": form,
        "magaza": magaza,
        "gunler": gunler,
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
