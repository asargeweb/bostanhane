"""
Üyelik formları: kayıt, giriş, hesap bilgileri, adres.

Telefon alanları bilerek geniş: müşteri "0533 444 55 66" yazar (14 karakter).
Kutuya ne yazılırsa yazılsın `telefon_duzelt` ile 10 haneye iner; modele
temizlenmiş hali gider.
"""

from django import forms
from django.contrib.auth import authenticate, password_validation
from django.utils import timezone

from core.models import Il, Ilce, Mahalle

from .models import Adres, Kullanici, Rol, telefon_dogrula, telefon_duzelt

TELEFON_KUTUSU = forms.TextInput(attrs={
    "inputmode": "tel", "autocomplete": "tel", "placeholder": "0533 123 45 67"})


def telefon_temizle(deger):
    telefon_dogrula(deger)
    return telefon_duzelt(deger)


class KayitFormu(forms.Form):
    telefon = forms.CharField(label="Telefon", max_length=20, widget=TELEFON_KUTUSU,
                              help_text="Girişte bu numarayı kullanacaksınız.")
    ad_soyad = forms.CharField(label="Ad soyad", max_length=120,
                               widget=forms.TextInput(attrs={"autocomplete": "name"}))
    sifre1 = forms.CharField(label="Şifre", strip=False,
                             widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}))
    sifre2 = forms.CharField(label="Şifre (tekrar)", strip=False,
                             widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}))
    eposta = forms.EmailField(label="E-posta", required=False,
                              widget=forms.EmailInput(attrs={
                                  "autocomplete": "email", "placeholder": "fatura ve bildirim için"}))
    # İki onay ayrı kutu ve ikincisi işaretsiz gelir: kampanya izni açık rıza
    # ister, KVKK aydınlatmasına iliştirilemez ve önceden işaretli olamaz.
    kvkk = forms.BooleanField(
        label="Aydınlatma metnini okudum, kişisel verilerimin işlenmesini kabul ediyorum.",
        error_messages={"required": "Üye olmak için aydınlatma metnini onaylamanız gerekiyor."})
    kosullar = forms.BooleanField(
        label="Üyelik ve Kullanım Koşulları'nı okudum, kabul ediyorum.",
        error_messages={"required": "Üye olmak için kullanım koşullarını kabul etmeniz gerekiyor."})
    duyuru_izni = forms.BooleanField(
        label="Kampanya ve indirim bildirimleri almak istiyorum.", required=False)

    def clean_telefon(self):
        telefon = telefon_temizle(self.cleaned_data["telefon"])
        if Kullanici.objects.filter(telefon=telefon).exists():
            raise forms.ValidationError(
                "Bu numarayla kayıtlı bir hesap var. Giriş yapmayı deneyin.")
        return telefon

    def clean(self):
        veri = super().clean()
        sifre1, sifre2 = veri.get("sifre1"), veri.get("sifre2")
        if sifre1 and sifre2 and sifre1 != sifre2:
            self.add_error("sifre2", "İki şifre aynı değil.")
        elif sifre1:
            # Benzerlik denetimi için geçici kullanıcı: şifre telefon ya da ad olmasın.
            gecici = Kullanici(telefon=veri.get("telefon", ""), ad_soyad=veri.get("ad_soyad", ""))
            try:
                password_validation.validate_password(sifre1, gecici)
            except forms.ValidationError as hata:
                self.add_error("sifre1", hata)
        return veri

    def kaydet(self):
        veri = self.cleaned_data
        return Kullanici.objects.create_user(
            telefon=veri["telefon"], password=veri["sifre1"],
            ad_soyad=veri["ad_soyad"].strip(), eposta=veri.get("eposta", ""),
            rol=Rol.UYE, kvkk_onayi=timezone.now(), duyuru_izni=veri["duyuru_izni"])


class GirisFormu(forms.Form):
    telefon = forms.CharField(label="Telefon", max_length=20, widget=TELEFON_KUTUSU)
    sifre = forms.CharField(label="Şifre", strip=False,
                            widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}))

    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        self.kullanici = None
        super().__init__(*args, **kwargs)

    def clean(self):
        veri = super().clean()
        telefon, sifre = veri.get("telefon"), veri.get("sifre")
        if telefon and sifre:
            self.kullanici = authenticate(self.request, username=telefon_duzelt(telefon),
                                          password=sifre)
            if self.kullanici is None:
                raise forms.ValidationError(
                    "Telefon numarası ya da şifre hatalı. Numarayı 0533 123 45 67 "
                    "biçiminde yazabilirsiniz.")
        return veri


class HesapFormu(forms.ModelForm):
    class Meta:
        model = Kullanici
        fields = ["ad_soyad", "eposta", "duyuru_izni"]
        labels = {"duyuru_izni": "Kampanya ve indirim bildirimleri almak istiyorum."}


class AdresFormu(forms.ModelForm):
    """
    İl → ilçe → mahalle sıralı seçim. Seçenekler sayfada JS ile doldurulur;
    sunucu tarafında da seçilen ilçeye göre daraltılıyor, yoksa binlerce mahalle
    tek açılır listeye dolardı.
    """

    il = forms.ModelChoiceField(label="İl", queryset=Il.objects.all(), empty_label="İl seçin")
    ilce = forms.ModelChoiceField(label="İlçe", queryset=Ilce.objects.none(),
                                  empty_label="İlçe seçin")
    baskasi_alacak = forms.BooleanField(label="Teslimatı başka biri alacak", required=False)
    teslim_telefonu = forms.CharField(label="Teslim alacak kişinin telefonu", max_length=20,
                                      required=False, widget=TELEFON_KUTUSU)

    class Meta:
        model = Adres
        fields = ["baslik", "il", "ilce", "mahalle", "acik_adres", "bina_no", "kat", "daire",
                  "tarif", "baskasi_alacak", "teslim_alacak", "teslim_telefonu"]
        widgets = {
            "acik_adres": forms.Textarea(attrs={"rows": 2,
                                                "placeholder": "Cadde, sokak, apartman adı"}),
            "tarif": forms.TextInput(attrs={"placeholder": "Zil çalışmıyor, arayın. Bakkalın üstü."}),
            "baslik": forms.TextInput(attrs={"placeholder": "Ev, İş, Annem"}),
        }

    def __init__(self, *args, uye=None, **kwargs):
        self.uye = uye
        super().__init__(*args, **kwargs)
        # Kutudaki örnek yazı yeterli; modelin yardım metni altında tekrar etmesin.
        for ad in ("baslik", "acik_adres", "tarif"):
            self.fields[ad].help_text = ""
        self.fields["mahalle"].empty_label = "Mahalle seçin"
        self.fields["mahalle"].queryset = Mahalle.objects.none()

        # Hangi il/ilçe seçili: gönderilen veri > kayıtlı adres > Beyşehir (pilot)
        il = ilce = None
        if self.is_bound:
            il = self._sec(Il, self.data.get("il"))
            ilce = self._sec(Ilce, self.data.get("ilce"))
        elif self.instance.pk:
            ilce = self.instance.mahalle.ilce
            il = ilce.il
            self.initial["baskasi_alacak"] = bool(self.instance.teslim_alacak
                                                  or self.instance.teslim_telefonu)
        else:
            ilce = (self._sec(Ilce, self.initial.get("ilce"))
                    or Ilce.objects.filter(il__ad="Konya", slug="beysehir").first())
            il = ilce.il if ilce else None
        if il:
            self.initial.setdefault("il", il.pk)
            self.fields["ilce"].queryset = Ilce.objects.filter(il=il)
        if ilce:
            self.initial.setdefault("ilce", ilce.pk)
            self.fields["mahalle"].queryset = Mahalle.objects.filter(ilce=ilce)

    @staticmethod
    def _sec(model, deger):
        return model.objects.filter(pk=deger).first() if str(deger or "").isdigit() else None

    def clean_baslik(self):
        baslik = self.cleaned_data["baslik"].strip()
        # Veritabanında üye + başlık tekil; silinen (kapatılan) adresler de sayılır.
        ayni = Adres.objects.filter(uye=self.uye, baslik__iexact=baslik)
        if self.instance.pk:
            ayni = ayni.exclude(pk=self.instance.pk)
        if ayni.exists():
            raise forms.ValidationError(f"“{baslik}” başlıklı bir adresiniz zaten var.")
        return baslik

    def clean_teslim_telefonu(self):
        deger = self.cleaned_data.get("teslim_telefonu", "")
        return telefon_temizle(deger) if deger.strip() else ""

    def clean(self):
        veri = super().clean()
        mahalle, ilce = veri.get("mahalle"), veri.get("ilce")
        if mahalle and ilce and mahalle.ilce_id != ilce.pk:
            self.add_error("mahalle", "Mahalle seçilen ilçede değil.")
        if not veri.get("baskasi_alacak"):
            veri["teslim_alacak"] = ""
            veri["teslim_telefonu"] = ""
        return veri

    def save(self, commit=True):
        adres = super().save(commit=False)
        adres.uye = self.uye
        adres.teslim_alacak = self.cleaned_data["teslim_alacak"]
        adres.teslim_telefonu = self.cleaned_data["teslim_telefonu"]
        if commit:
            adres.save()
        return adres


class CokluResim(forms.ClearableFileInput):
    allow_multiple_selected = True


class MahallemeGelinFormu(forms.Form):
    """
    "Mahallemde de Bostanhane olsun" talebi. Üyelik istemez.

    Mahalle listesi yüklü ilçede resmî mahalle seçilir; yüklü olmayanda adı
    serbest yazılır. Seçim zorunlu: talep haritası mahalleye göre sayıyor,
    ilçesiz/mahallesiz kayıt haritada "yer bilgisi yok" diye boşa düşer.
    """

    # Yalnızca ilçeleri yüklü iller: ilçesiz kayıt haritada bir yere oturmaz.
    # Yeni il eklendikçe (cografya_yukle) listeye kendiliğinden girer.
    il = forms.ModelChoiceField(label="İl", empty_label="İl seçin",
                                queryset=Il.objects.filter(ilceler__isnull=False).distinct())
    ilce = forms.ModelChoiceField(label="İlçe", queryset=Ilce.objects.none(),
                                  empty_label="İlçe seçin")
    mahalle = forms.ModelChoiceField(label="Mahalle", queryset=Mahalle.objects.none(),
                                     empty_label="Mahalle seçin", required=False)
    mahalle_adi = forms.CharField(label="Mahalleniz", max_length=80, required=False,
                                  widget=forms.TextInput(attrs={"placeholder": "Örnek: Kızılay"}))
    ad_soyad = forms.CharField(label="Ad soyad", max_length=120,
                               widget=forms.TextInput(attrs={"autocomplete": "name"}))
    telefon = forms.CharField(label="Telefon", max_length=20, widget=TELEFON_KUTUSU)
    eposta = forms.EmailField(label="E-posta", required=False,
                              widget=forms.EmailInput(attrs={"autocomplete": "email"}))
    kvkk = forms.BooleanField(
        label="Aydınlatma metnini okudum; mahalleme gelindiğinde bana ulaşılmasını kabul ediyorum.",
        error_messages={"required": "Size haber verebilmemiz için aydınlatma metnini "
                                    "onaylamanız gerekiyor."})

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Seçenekleri seçilen il/ilçeye göre daralt; yoksa sunucu binlerce
        # mahalleyi tek listeye basar. Varsayılan Beyşehir (pilot).
        il = ilce = None
        if self.is_bound:
            il = AdresFormu._sec(Il, self.data.get("il"))
            ilce = AdresFormu._sec(Ilce, self.data.get("ilce"))
        else:
            ilce = Ilce.objects.filter(il__ad="Konya", slug="beysehir").first()
            il = ilce.il if ilce else None
        if il:
            self.initial.setdefault("il", il.pk)
            self.fields["ilce"].queryset = Ilce.objects.filter(il=il)
        if ilce:
            self.initial.setdefault("ilce", ilce.pk)
            self.fields["mahalle"].queryset = Mahalle.objects.filter(ilce=ilce)
        self.mahalle_listesi_var = bool(ilce and ilce.mahalleler.exists())
        # Hangisi zorunlu ilçeye göre değişiyor; etiketteki "isteğe bağlı" yanıltmasın.
        self.fields["mahalle"].required = self.mahalle_listesi_var
        self.fields["mahalle_adi"].required = not self.mahalle_listesi_var
        self.fields["mahalle"].error_messages["required"] = "Mahallenizi seçin."
        self.fields["mahalle_adi"].error_messages["required"] = "Mahallenizin adını yazın."

    def clean_telefon(self):
        return telefon_temizle(self.cleaned_data["telefon"])

    def clean_ad_soyad(self):
        return self.cleaned_data["ad_soyad"].strip()

    def clean(self):
        veri = super().clean()
        ilce = veri.get("ilce")
        if ilce is None:
            return veri
        # Gizli kalan kutudan bir şey gelse de yalnızca geçerli olan saklanır.
        if self.mahalle_listesi_var:
            veri["mahalle_adi"] = ""
        else:
            veri["mahalle"] = None
            veri["mahalle_adi"] = (veri.get("mahalle_adi") or "").strip()
            if not veri["mahalle_adi"] and "mahalle_adi" not in self.errors:
                self.add_error("mahalle_adi", "Mahallenizin adını yazın.")
        return veri


class CokluResimAlani(forms.ImageField):
    """Birden çok resim; her biri ImageField denetiminden (gerçekten resim mi) geçer."""

    widget = CokluResim

    def clean(self, veri, ilk=None):
        tek = super().clean
        if isinstance(veri, (list, tuple)):
            return [tek(d, ilk) for d in veri if d]
        return [tek(veri, ilk)] if veri else []


class TalepFormu(forms.Form):
    """
    "Bir sorun var": hangi ürün, ne sorunu, açıklama, fotoğraf.

    Fotoğraf alanı yalnızca nesne depolama varken eklenir (`gorsel_yuklenebilir_mi`):
    canlıda disk kalıcı değil, kanıt sessizce kaybolmasın.
    """

    EN_FAZLA_FOTOGRAF = 3
    EN_BUYUK_BOYUT = 5 * 1024 * 1024

    kalem = forms.ChoiceField(label="Hangi ürün?", required=False)
    tur = forms.ChoiceField(label="Sorun ne?", widget=forms.RadioSelect)
    aciklama = forms.CharField(
        label="Ne oldu?", max_length=1000,
        widget=forms.Textarea(attrs={"rows": 3, "placeholder": "Örnek: Domatesler ezilmiş, ikisi çürük."}))

    def __init__(self, *args, siparis=None, fotograf=False, **kwargs):
        from talep.models import Talep
        super().__init__(*args, **kwargs)
        self.siparis = siparis
        self.fields["kalem"].choices = [("", "Siparişin geneli")] + [
            (str(k.pk), k.urun_adi) for k in siparis.kalemler.all()]
        self.fields["tur"].choices = Talep.Tur.choices
        if fotograf:
            self.fields["fotograflar"] = CokluResimAlani(
                label="Fotoğraf", required=False,
                help_text="En fazla 3 fotoğraf, her biri en fazla 5 MB.",
                widget=CokluResim(attrs={"accept": "image/*", "multiple": True}))

    def clean_kalem(self):
        pk = self.cleaned_data.get("kalem")
        if not pk:
            return None
        kalem = self.siparis.kalemler.filter(pk=pk).first()
        if kalem is None:
            raise forms.ValidationError("Seçilen ürün bu siparişte yok.")
        return kalem

    def clean_fotograflar(self):
        resimler = self.cleaned_data.get("fotograflar") or []
        if len(resimler) > self.EN_FAZLA_FOTOGRAF:
            raise forms.ValidationError(f"En fazla {self.EN_FAZLA_FOTOGRAF} fotoğraf ekleyebilirsiniz.")
        for resim in resimler:
            if resim.size > self.EN_BUYUK_BOYUT:
                raise forms.ValidationError(f"“{resim.name}” 5 MB'tan büyük.")
        return resimler
