"""
Bostanhane — hesaplar uygulaması yönetim paneli

Bu dosya `hesaplar/admin.py` yerine geçer.

Django'nun hazır kullanıcı paneli "kullanıcı adı" bekler; bizde giriş anahtarı
telefon. Bu yüzden ekleme ve düzenleme formlarını kendimiz yazıyoruz.

Şifreler hiçbir zaman okunabilir halde durmaz. Panelde şifre kutusu değil,
"şifreyi değiştir" bağlantısı görünür — Django'nun kendi davranışı budur.
"""

from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.contrib.auth.password_validation import validate_password
from django.db.models import Q

from core.admin_araclar import MagazaKisitliAdmin, liste_filtrelerini_daralt

from .models import Adres, Kullanici, Rol, telefon_dogrula, telefon_duzelt


# Panelde telefon kutusu geniş olsun: kullanıcı "0532 111 22 33" diye de
# yazabilsin. Modelin alanı 10 hane; kaydetmeden önce biçimi düzeltiyoruz.
# Bu kutu olmasaydı boşluklu yazım "en fazla 10 karakter" hatası verirdi.
def telefon_kutusu():
    return forms.CharField(
        label="Telefon", max_length=20,
        help_text="0532 111 22 33 ya da 5321112233 — ikisi de olur.")


def telefon_temizle(deger):
    duzeltilmis = telefon_duzelt(deger)
    telefon_dogrula(duzeltilmis)
    return duzeltilmis


# --------------------------------------------------------------------------
# Formlar
# --------------------------------------------------------------------------
class KullaniciOlusturmaFormu(forms.ModelForm):
    """Yeni kullanıcı eklerken kullanılır. Şifre iki kez sorulur."""

    telefon = telefon_kutusu()
    sifre1 = forms.CharField(label="Şifre", widget=forms.PasswordInput, strip=False,
                             help_text="En az 8 karakter. Sadece rakam olmasın.")
    sifre2 = forms.CharField(label="Şifre (tekrar)", widget=forms.PasswordInput, strip=False)

    class Meta:
        model = Kullanici
        fields = ("telefon", "ad_soyad", "eposta", "rol", "magaza")

    def clean_telefon(self):
        return telefon_temizle(self.cleaned_data["telefon"])

    def clean_sifre2(self):
        sifre1 = self.cleaned_data.get("sifre1")
        sifre2 = self.cleaned_data.get("sifre2")
        if sifre1 and sifre2 and sifre1 != sifre2:
            raise forms.ValidationError("İki şifre birbirinden farklı.")
        validate_password(sifre2)
        return sifre2

    def save(self, commit=True):
        kullanici = super().save(commit=False)
        kullanici.set_password(self.cleaned_data["sifre2"])
        if commit:
            kullanici.save()
        return kullanici


class KullaniciDegistirmeFormu(forms.ModelForm):
    """Var olan kullanıcıyı düzenlerken kullanılır."""

    telefon = telefon_kutusu()
    password = ReadOnlyPasswordHashField(
        label="Şifre",
        help_text="Şifreler okunabilir halde saklanmaz. "
                  "Değiştirmek için <a href=\"../password/\">bu bağlantıyı</a> kullanın.")

    class Meta:
        model = Kullanici
        fields = "__all__"

    def clean_telefon(self):
        return telefon_temizle(self.cleaned_data["telefon"])


# --------------------------------------------------------------------------
# Adres — kullanıcının içinde satır olarak
# --------------------------------------------------------------------------
class AdresFormu(forms.ModelForm):
    """Teslimat telefonu da boşluklu yazılabilsin."""

    teslim_telefonu = forms.CharField(
        label="Teslimat telefonu", max_length=20, required=False,
        help_text="Boşsa üyenin telefonu kullanılır.")

    class Meta:
        model = Adres
        fields = "__all__"

    def clean_teslim_telefonu(self):
        deger = self.cleaned_data.get("teslim_telefonu")
        return telefon_temizle(deger) if deger else ""


class AdresSatiri(admin.StackedInline):
    model = Adres
    form = AdresFormu
    extra = 0
    fk_name = "uye"
    verbose_name = "adres"
    verbose_name_plural = "adresler"
    fields = (
        ("baslik", "mahalle", "varsayilan"),
        "acik_adres",
        ("bina_no", "kat", "daire"),
        ("teslim_alacak", "teslim_telefonu"),
        "tarif",
        ("enlem", "boylam"),
        "aktif",
    )


# --------------------------------------------------------------------------
# Kullanıcı paneli
# --------------------------------------------------------------------------
@admin.register(Kullanici)
class KullaniciAdmin(UserAdmin):
    add_form = KullaniciOlusturmaFormu
    form = KullaniciDegistirmeFormu
    inlines = [AdresSatiri]

    ordering = ("ad_soyad",)
    list_display = ("ad_soyad", "telefon_gosterim", "rol", "magaza", "is_active", "olusturuldu")
    list_filter = ("rol", "magaza", "is_active", "telefon_dogrulandi")
    search_fields = ("ad_soyad", "telefon", "eposta")
    list_select_related = ("magaza",)
    date_hierarchy = "olusturuldu"

    fieldsets = (
        (None, {"fields": ("telefon", "password")}),
        ("Kişi", {"fields": ("ad_soyad", "eposta")}),
        ("Görev", {"fields": ("rol", "magaza")}),
        ("Durum", {"fields": ("is_active", "telefon_dogrulandi", "duyuru_izni", "kvkk_onayi")}),
        ("Yetkiler", {
            "classes": ("collapse",),
            "description": "Bu bölüme normalde dokunmanız gerekmez; "
                           "panele giriş hakkı rol seçimine göre ayarlanır.",
            "fields": ("is_staff", "is_superuser", "groups", "user_permissions"),
        }),
        ("Kayıt bilgisi", {
            "classes": ("collapse",),
            "fields": ("last_login", "olusturuldu", "guncellendi"),
        }),
    )
    add_fieldsets = (
        (None, {
            "description": "Telefon 10 hane olarak girilir, başında sıfır olmadan: 5321112233",
            "fields": ("telefon", "ad_soyad", "eposta", "rol", "magaza", "sifre1", "sifre2"),
        }),
    )
    readonly_fields = ("last_login", "olusturuldu", "guncellendi")

    @admin.display(description="telefon", ordering="telefon")
    def telefon_gosterim(self, nesne):
        return nesne.telefon_okunur

    def get_list_filter(self, request):
        # "Mağazaya göre" süzgecinde başka mağazaların adları görünmesin
        return liste_filtrelerini_daralt(self, request, super().get_list_filter(request))

    @staticmethod
    def _tumunu_gorur(request):
        return bool(getattr(request.user, "tum_magazalari_gorur", request.user.is_superuser))

    def get_fieldsets(self, request, obj=None):
        """
        "Yetkiler" bölümünü yalnızca süper admin görür.
        Aksi halde bir mağaza yöneticisi kendine süper admin kutucuğunu
        işaretleyip bütün mağazaları açabilirdi.
        """
        bolumler = super().get_fieldsets(request, obj)
        if not self._tumunu_gorur(request):
            bolumler = tuple(b for b in bolumler if b[0] != "Yetkiler")
        return bolumler

    # Yeni kullanıcı eklenirken adres satırı gösterilmesin;
    # kayıt henüz yok, adres bağlanacak kişi belirsiz.
    def get_inline_instances(self, request, obj=None):
        if obj is None:
            return []
        return super().get_inline_instances(request, obj)

    # -- mağaza izolasyonu -------------------------------------------------
    def get_queryset(self, request):
        """
        Mağaza yöneticisi kimi görür? Kendi mağazasının personelini ve
        kendi mağazasının mahallelerinde adresi olan üyeleri.
        """
        sorgu = super().get_queryset(request)
        if self._tumunu_gorur(request):
            return sorgu
        magaza = getattr(request.user, "magaza", None)
        if magaza is None:
            return sorgu.none()
        return sorgu.filter(
            Q(magaza=magaza) | Q(rol=Rol.UYE, adresler__mahalle__hizmet_kayitlari__magaza=magaza)
        ).distinct()

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "magaza":
            if not self._tumunu_gorur(request):
                magaza = getattr(request.user, "magaza", None)
                if magaza is not None:
                    kwargs["queryset"] = db_field.remote_field.model.objects.filter(pk=magaza.pk)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def formfield_for_choice_field(self, db_field, request, **kwargs):
        """Mağaza yöneticisi süper admin oluşturamaz."""
        if db_field.name == "rol":
            if not self._tumunu_gorur(request):
                kwargs["choices"] = [
                    (deger, etiket) for deger, etiket in Rol.choices
                    if deger != Rol.SUPER_ADMIN
                ]
        return super().formfield_for_choice_field(db_field, request, **kwargs)


# --------------------------------------------------------------------------
# Adres paneli (ayrı liste; kurye ve paketleme için arama kolaylığı)
# --------------------------------------------------------------------------
@admin.register(Adres)
class AdresAdmin(MagazaKisitliAdmin, admin.ModelAdmin):
    magaza_yolu = "mahalle__hizmet_kayitlari__magaza"
    form = AdresFormu

    list_display = ("uye", "baslik", "mahalle", "varsayilan", "aktif")
    list_filter = ("mahalle__ilce__il", "mahalle__ilce", "varsayilan", "aktif")
    search_fields = ("uye__ad_soyad", "uye__telefon", "acik_adres", "tarif")
    list_select_related = ("uye", "mahalle")
    autocomplete_fields = ("uye",)
    fieldsets = (
        (None, {"fields": ("uye", "baslik", "varsayilan", "aktif")}),
        ("Adres", {"fields": ("mahalle", "acik_adres", ("bina_no", "kat", "daire"), "tarif")}),
        ("Teslim alacak kişi", {
            "description": "Boş bırakılırsa üyenin kendi adı ve telefonu kullanılır.",
            "fields": ("teslim_alacak", "teslim_telefonu"),
        }),
        ("Harita", {"classes": ("collapse",), "fields": (("enlem", "boylam"),)}),
    )

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """
        Mağaza yöneticisi adresi kendi personeline veya bir üyeye bağlayabilir;
        başka mağazanın personeline bağlayamaz.

        Üyeler kısıtlanmıyor: yeni kaydolmuş, henüz adresi olmayan bir üyeye
        adres girilebilsin diye. (Hangi mağazaya düştüğü zaten seçilen
        mahalleden belli olur.)
        """
        if db_field.name == "uye" and not self.tum_magazalari_gorur(request):
            magaza = self.kullanicinin_magazasi(request)
            if magaza is not None:
                kwargs["queryset"] = Kullanici.objects.filter(
                    Q(magaza=magaza) | Q(rol=Rol.UYE)
                )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
