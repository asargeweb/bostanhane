from django.urls import path

from . import views

urlpatterns = [
    path("sepet/", views.sepet, name="sepet"),
    path("sepet/ekle/<int:pk>/", views.sepete_ekle, name="sepete_ekle"),
    path("sepet/kalem/<int:pk>/", views.kalem_guncelle, name="kalem_guncelle"),
    path("sepet/teslimat/", views.teslimat_sec, name="teslimat_sec"),
    path("sepet/siparis-ver/", views.siparis_ver, name="siparis_ver"),
]
