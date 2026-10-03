"""
Bostanhane — talep paneli

Bu dosya `talep/admin.py` olarak kaydedilir.

Mağaza yöneticisi kararı buradan veriyor. Karar bir alan değişikliği değil,
para hareketi: form `talep.islemler.karara_bagla`'yı çağırıyor, o da iadeyi
sağlayıcıya gönderip deftere yazıyor.

`durum` ve `iade_tutari` alanlarını **doğrudan düzenlenebilir yapmıyoruz** —
elle "kabul" yazılırsa para gönderilmeden talep kapanırdı. Karar yalnızca
aşağıdaki formdan veriliyor.
"""

from django import forms
from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.http import HttpResponseRedirect
from django.utils.html import format_html, format_html_join
from django.utils.safestring import mark_safe

from core.admin_araclar import MagazaKisitliAdmin
from core.araclar import para_yaz

from .islemler import karara_bagla
from .models import Talep, TalepGorseli

DURUM_RENKLERI = {
    Talep.Durum.ACIK: "#B23A24",
    Talep.Durum.INCELENIYOR: "#8A5A12",
    Talep.Durum.KABUL: "#2E6B2A",
    Talep.Durum.KISMI: "#2E6B2A",
    Talep.Durum.RED: "#5B675A",
}


class TalepGorseliSatiri(admin.TabularInline):
    model = TalepGorseli
    extra = 0
    fields = ("onizleme", "gorsel", "sira")
    readonly_fields = ("onizleme",)
    can_delete = False

    @admin.display(description="fotoğraf")
    def onizleme(self, nesne):
        if not nesne.gorsel:
            return "—"
        return format_html(
            '<a href="{}" target="_blank" rel="noopener">'
            '<img src="{}" style="max-height:140px;border-radius:8px"></a>',
            nesne.gorsel.url, nesne.gorsel.url)

    def has_add_permission(self, request, obj=None):
        """Fotoğrafı müşteri yükler; panelden eklenmez."""
        return False


class KararFormu(forms.ModelForm):
    """
    Karar formu. `durum` ve `iade_tutari` modele doğrudan yazılmıyor;
    `save_model` bunları `karara_bagla`'ya veriyor.
    """

    karar = forms.ChoiceField(
        label="Karar", required=False,
        choices=[("", "— karar verme, şimdilik dursun —"),
                 (Talep.Durum.INCELENIYOR, "İnceleniyor olarak işaretle"),
                 (Talep.Durum.KABUL, "Kabul et — tamamını iade et"),
                 (Talep.Durum.KISMI, "Kısmen kabul et — bir kısmını iade et"),
                 (Talep.Durum.RED, "Reddet — iade yok")],
        help_text="Kabul kararında aşağıdaki tutar müşterinin kartına iade edilir.")
    iade = forms.DecimalField(label="İade edilecek tutar (₺)", max_digits=10,
                              decimal_places=2, required=False, min_value=0)

    class Meta:
        model = Talep
        fields = ("karar_notu",)

    def clean(self):
        veri = super().clean()
        karar = veri.get("karar")
        if karar in (Talep.Durum.KABUL, Talep.Durum.KISMI) and not veri.get("iade"):
            self.add_error("iade", "Kabul kararında iade tutarı yazılmalı.")
        if karar and karar != Talep.Durum.INCELENIYOR and not (veri.get("karar_notu") or "").strip():
            self.add_error("karar_notu", "Müşteriye bir açıklama yazın.")
        return veri


@admin.register(Talep)
class TalepAdmin(MagazaKisitliAdmin, admin.ModelAdmin):
    magaza_yolu = "siparis__magaza"
    form = KararFormu

    list_display = ("olusturuldu", "siparis_no", "urun", "tur",
                    "durum_gosterim", "iade_gosterim", "fotograf_adedi")
    list_filter = ("durum", "tur", "siparis__magaza", "olusturuldu")
    search_fields = ("siparis__numara", "aciklama", "siparis__uye__ad_soyad",
                     "siparis__uye__telefon")
    list_select_related = ("siparis", "siparis__uye", "kalem")
    date_hierarchy = "olusturuldu"
    inlines = [TalepGorseliSatiri]
    readonly_fields = ("ozet", "siparis", "kalem", "tur", "aciklama", "durum",
                       "iade_tutari", "karar_veren", "karar_zamani",
                       "olusturuldu", "guncellendi")
    fieldsets = (
        (None, {"fields": ("ozet",)}),
        ("Müşterinin bildirimi", {
            "fields": (("siparis", "kalem"), "tur", "aciklama", "olusturuldu")}),
        ("Karar", {
            "description": "Kabul kararında para müşterinin kartına iade edilir ve "
                           "ödeme defterine yazılır. Bu işlem geri alınamaz.",
            "fields": ("karar", "iade", "karar_notu")}),
        ("Verilmiş karar", {"classes": ("collapse",),
                            "fields": (("durum", "iade_tutari"),
                                       ("karar_veren", "karar_zamani"))}),
    )

    # -- sütunlar ----------------------------------------------------------
    @admin.display(description="sipariş", ordering="siparis__numara")
    def siparis_no(self, nesne):
        return nesne.siparis.numara

    @admin.display(description="ürün")
    def urun(self, nesne):
        return nesne.kalem.urun_adi if nesne.kalem_id else "sipariş geneli"

    @admin.display(description="durum", ordering="durum")
    def durum_gosterim(self, nesne):
        return format_html('<b style="color:{}">{}</b>',
                           DURUM_RENKLERI.get(nesne.durum, "#5B675A"),
                           nesne.get_durum_display())

    @admin.display(description="iade", ordering="iade_tutari")
    def iade_gosterim(self, nesne):
        return para_yaz(nesne.iade_tutari) if nesne.iade_tutari else "—"

    @admin.display(description="fotoğraf")
    def fotograf_adedi(self, nesne):
        return nesne.gorseller.count() or "—"

    @admin.display(description="özet")
    def ozet(self, nesne):
        if nesne.pk is None:
            return "—"
        satirlar = [
            format_html("Müşteri: <b>{}</b> · {}", nesne.siparis.uye.ad_soyad,
                        nesne.siparis.teslim_telefon),
            format_html("Sipariş tutarı: <b>{}</b> · çekilen: <b>{}</b>",
                        para_yaz(nesne.siparis.toplam),
                        para_yaz(nesne.siparis.cekilen_tutar)),
            format_html("Bu talep için en fazla <b>{}</b> iade edilebilir.",
                        para_yaz(nesne.en_fazla_iade)),
        ]
        if nesne.karara_baglandi_mi:
            satirlar.append(format_html(
                '<span style="color:#2E6B2A">Karar verildi: {} · {}</span>',
                nesne.get_durum_display(), para_yaz(nesne.iade_tutari)))
        return format_html_join(mark_safe("<br>"), "{}", ((s,) for s in satirlar))

    # -- kaydetme ----------------------------------------------------------
    def save_model(self, request, obj, form, change):
        """
        Kararı `karara_bagla` veriyor — para oradan gidiyor.

        Karar seçilmemişse yalnızca not kaydediliyor; talep açık kalıyor.
        """
        karar = form.cleaned_data.get("karar")
        if not karar:
            obj.save(update_fields=["karar_notu", "guncellendi"])
            return

        if karar == Talep.Durum.INCELENIYOR:
            obj.durum = Talep.Durum.INCELENIYOR
            obj.save(update_fields=["durum", "karar_notu", "guncellendi"])
            messages.info(request, "Talep 'inceleniyor' olarak işaretlendi.")
            return

        try:
            talep = karara_bagla(obj, karar, kullanici=request.user,
                                 karar_notu=form.cleaned_data.get("karar_notu"),
                                 iade_tutari=form.cleaned_data.get("iade"))
        except ValidationError as hata:
            # Hatayı yutmuyoruz: para gitmediyse yönetici bilmeli.
            messages.error(request, " ".join(hata.messages))
            request._talep_karar_hatasi = True
            return
        if talep.iade_tutari:
            messages.success(request, f"Karar kaydedildi; müşterinin kartına "
                                      f"{para_yaz(talep.iade_tutari)} iade edildi.")
        else:
            messages.success(request, "Karar kaydedildi.")

    def response_change(self, request, obj):
        """
        İade başarısızsa Django'nun "başarıyla değiştirildi" mesajını bastırır.

        Django kaydetmeden sonra kendi başarı mesajını ekliyor; biz hata mesajı
        basmışsak yönetici iki çelişkili cümle görüyordu — "iade yapılamadı" ve
        "başarıyla değiştirildi" yan yana. Para işinde bu kabul edilemez.
        (Claude Code 3 Ekim'de yakaladı.)
        """
        if getattr(request, "_talep_karar_hatasi", False):
            return HttpResponseRedirect(request.get_full_path())
        return super().response_change(request, obj)

    def has_add_permission(self, request):
        """Talebi müşteri açar; panelden açılmaz."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Şikâyet kaydı silinmez — anlaşmazlıkta kanıt."""
        return False
