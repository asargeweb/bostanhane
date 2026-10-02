"""
Bostanhane — adres yönlendirmeleri

Bu dosya `bostanhane/urls.py` yerine geçer.

Yönetim paneli /admin/ yerine /yonetim/ adresinde. Sebebi güvenlik:
internetteki otomatik saldırı araçları en çok /admin/ adresini dener.
"""

from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static

from core import views as core_views

urlpatterns = [
    path("", core_views.ana_sayfa, name="ana_sayfa"),
    path("yonetim/", admin.site.urls),
    path("", include("hesaplar.urls")),
    path("", include("katalog.urls")),
    path("", include("siparis.urls")),
    path("", include("depo.urls")),
    path("", include("lojistik.urls")),
]

# Yasal metinler girişsiz açılır: sözleşmeyi okumak için üye olmak gerekmez.
YASAL_SAYFALAR = [
    ("aydinlatma-metni/", "aydinlatma", "yasal_aydinlatma"),
    ("kullanim-kosullari/", "kullanim", "yasal_kullanim"),
    ("gizlilik-politikasi/", "gizlilik", "yasal_gizlilik"),
    ("on-bilgilendirme-formu/", "on_bilgilendirme", "yasal_on_bilgilendirme"),
    ("mesafeli-satis-sozlesmesi/", "mesafeli_satis", "yasal_mesafeli_satis"),
    ("iptal-ve-iade/", "iade", "yasal_iade"),
]
urlpatterns += [
    path(adres, TemplateView.as_view(template_name=f"yasal/{sablon}.html"), name=ad)
    for adres, sablon, ad in YASAL_SAYFALAR
]

# Geliştirme sırasında ürün görsellerinin görünmesi için
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
