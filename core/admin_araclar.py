"""
Bostanhane — yönetim paneli için ortak araçlar

Bu dosya `core/admin_araclar.py` olarak kaydedilir.

Burada tek bir iş yapılıyor: **mağaza izolasyonu**.

Kural şu: süper admin bütün mağazaları görür, diğer personel yalnızca kendi
mağazasını. Bunu şablonda gizlemek yeterli değil — adres çubuğuna başka bir
kaydın numarasını yazan biri onu görebilirdi. O yüzden kısıtlama *sorgu
seviyesinde* uygulanır: kullanıcının göremeyeceği kayıt veritabanından hiç
gelmez.

Kullanımı:

    from core.admin_araclar import MagazaKisitliAdmin

    @admin.register(Urun)
    class UrunAdmin(MagazaKisitliAdmin, admin.ModelAdmin):
        magaza_yolu = "magaza"          # kayıttan mağazaya giden yol

`magaza_yolu` kayıttan mağazaya nasıl gidildiğini söyler:
    Urun.magaza            → "magaza"
    Adres.mahalle.magaza   → "mahalle__magaza"
    Magaza (kendisi)       → "pk"
"""

from django.contrib import admin
from django.contrib.admin.utils import NotRelationField, get_fields_from_path
from django.core.exceptions import FieldDoesNotExist


def tum_magazalari_gorur(request):
    kullanici = request.user
    return bool(getattr(kullanici, "tum_magazalari_gorur", kullanici.is_superuser))


def liste_filtrelerini_daralt(model_admin, request, filtreler):
    """
    Listenin sağındaki "mağazaya / mahalleye göre" süzgeçlerini daraltır.

    Django bu kutulara normalde tablodaki BÜTÜN mağazaları ve mahalleleri
    koyar; kayıtları süzsek bile başka mağazaların adları orada görünürdü.
    İlişkili alan süzgeçlerini `RelatedOnlyFieldListFilter`'a çeviriyoruz:
    o yalnızca kullanıcının zaten görebildiği kayıtlarda geçen değerleri listeler.
    """
    if tum_magazalari_gorur(request):
        return filtreler
    daraltilmis = []
    for filtre in filtreler:
        if isinstance(filtre, str):
            try:
                alan = get_fields_from_path(model_admin.model, filtre)[-1]
            except (FieldDoesNotExist, NotRelationField):
                alan = None
            if alan is not None and alan.is_relation:
                filtre = (filtre, admin.RelatedOnlyFieldListFilter)
        daraltilmis.append(filtre)
    return daraltilmis


class MagazaKisitliAdmin:
    """
    Yönetim paneli listelerini kullanıcının mağazasına göre süzer.

    `admin.ModelAdmin`'den ÖNCE yazılmalı:
        class XAdmin(MagazaKisitliAdmin, admin.ModelAdmin)
    Python yöntemleri soldan sağa arar; böylece buradaki get_queryset önce çalışır.
    """

    magaza_yolu = "magaza"

    # Hangi seçim kutuları mağazaya göre süzülecek (model adları, küçük harf).
    # Yeni uygulama eklendikçe alt sınıfta genişletilir:
    #     suzulecek_modeller = ("magaza", "mahalle", "urun")
    # Buraya yazılmayan model süzülmez. Sebebi: kullanıcı gibi bazı modellerde
    # `magaza` alanı boş olur (üyeler mağazaya bağlanmaz); körlemesine süzmek
    # onları seçilemez hale getirirdi.
    # "hizmetmahallesi": teslim günü ve takvim eklerken başka mağazanın
    # hizmet mahallesi seçilemesin.
    suzulecek_modeller = ("magaza", "mahalle", "hizmetmahallesi")

    # -- yardımcılar -------------------------------------------------------
    def tum_magazalari_gorur(self, request):
        return tum_magazalari_gorur(request)

    def kullanicinin_magazasi(self, request):
        return getattr(request.user, "magaza", None)

    # -- liste süzgeci -----------------------------------------------------
    def get_queryset(self, request):
        sorgu = super().get_queryset(request)
        if self.tum_magazalari_gorur(request):
            return sorgu
        magaza = self.kullanicinin_magazasi(request)
        if magaza is None:
            # Mağazası olmayan personel hiçbir kayıt görmez.
            # Açık kapı bırakmaktan iyidir; eksik veri panelde hemen fark edilir.
            return sorgu.none()
        # distinct(): mağazaya giden yol ters ilişkiden geçebiliyor
        # (adres → mahalle → hizmet kayıtları → mağaza) ve aynı kayıt
        # birden fazla kez dönebilir.
        # Mağaza modelinin kendisinde yol "pk"dir; orada nesne değil numara verilir.
        deger = magaza.pk if self.magaza_yolu == "pk" else magaza
        return sorgu.filter(**{self.magaza_yolu: deger}).distinct()

    def get_list_filter(self, request):
        return liste_filtrelerini_daralt(self, request, super().get_list_filter(request))

    # -- seçim kutuları ----------------------------------------------------
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """
        Mağaza ve mahalle seçim kutularını da süzer. Aksi halde bir mağaza
        yöneticisi, kaydını başka mağazanın mahallesine bağlayabilirdi.
        """
        if not self.tum_magazalari_gorur(request):
            magaza = self.kullanicinin_magazasi(request)
            if magaza is not None:
                hedef = db_field.remote_field.model
                ad = hedef._meta.model_name
                if ad in self.suzulecek_modeller:
                    if ad == "magaza":
                        kwargs["queryset"] = hedef.objects.filter(pk=magaza.pk)
                    elif self._alan_var_mi(hedef, "magaza"):
                        kwargs["queryset"] = hedef.objects.filter(magaza=magaza)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    @staticmethod
    def _alan_var_mi(model, alan_adi):
        try:
            model._meta.get_field(alan_adi)
            return True
        except FieldDoesNotExist:
            return False

    # -- kaydetme ----------------------------------------------------------
    def save_model(self, request, nesne, form, degisti):
        """Mağaza alanı boş bırakılırsa kullanıcının mağazası yazılır."""
        if not self.tum_magazalari_gorur(request):
            magaza = self.kullanicinin_magazasi(request)
            if magaza is not None and self._alan_var_mi(nesne.__class__, "magaza"):
                if getattr(nesne, "magaza_id", None) is None:
                    nesne.magaza = magaza
        super().save_model(request, nesne, form, degisti)
