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

from .models import IlgiKaydi, Magaza


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
    mahalleler = []
    if magaza:
        # Hizmet verilen mahalleler; `ad` ve `teslim_gunleri_metni` şablonda
        # mahalle gibi davranıyor, bu yüzden şablonu değiştirmek gerekmedi.
        mahalleler = (magaza.hizmet_mahalleleri
                      .filter(aktif=True)
                      .select_related("mahalle")
                      .prefetch_related("haftalik_gunler"))

    return render(request, "core/ana_sayfa.html", {
        "form": form,
        "magaza": magaza,
        "mahalleler": mahalleler,
    })
