from django.urls import path

from . import views

urlpatterns = [
    path("kayit/", views.kayit, name="kayit"),
    path("giris/", views.giris, name="giris"),
    path("cikis/", views.cikis, name="cikis"),
    path("hesabim/", views.hesabim, name="hesabim"),
    path("hesabim/adresler/", views.adresler, name="adresler"),
    path("hesabim/adresler/yeni/", views.adres_formu, name="adres_ekle"),
    path("hesabim/adresler/<int:pk>/", views.adres_formu, name="adres_duzenle"),
    path("hesabim/adresler/haber-ver/", views.adres_ilgi, name="adres_ilgi"),
    path("hesabim/adresler/<int:pk>/varsayilan/", views.adres_varsayilan, name="adres_varsayilan"),
    path("hesabim/adresler/<int:pk>/sil/", views.adres_sil, name="adres_sil"),
    path("hesabim/siparisler/", views.siparislerim, name="siparislerim"),
    path("hesabim/siparisler/<str:numara>/", views.siparis_detay, name="siparis_detay"),
    path("hesabim/siparisler/<str:numara>/iptal/", views.siparis_iptal, name="siparis_iptal"),
    path("hesabim/siparisler/<str:numara>/sozlesme/", views.siparis_sozlesmesi, name="siparis_sozlesmesi"),
    path("hesabim/siparisler/<str:numara>/teslim-onayi/", views.teslim_onayi, name="teslim_onayi"),
    path("adres/ilceler/", views.ilceler, name="adres_ilceler"),
    path("adres/mahalleler/", views.mahalleler, name="adres_mahalleler"),
    path("adres/mahalle/<int:pk>/", views.mahalle_bilgi, name="adres_mahalle_bilgi"),
]
