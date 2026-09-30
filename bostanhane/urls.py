"""
Bostanhane — adres yönlendirmeleri

Bu dosya `bostanhane/urls.py` yerine geçer.

Yönetim paneli /admin/ yerine /yonetim/ adresinde. Sebebi güvenlik:
internetteki otomatik saldırı araçları en çok /admin/ adresini dener.
"""

from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from core import views as core_views

urlpatterns = [
    path("", core_views.ana_sayfa, name="ana_sayfa"),
    path("yonetim/", admin.site.urls),
]

# Geliştirme sırasında ürün görsellerinin görünmesi için
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
