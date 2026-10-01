from django.urls import path

from . import views

urlpatterns = [
    path("urunler/", views.vitrin, name="vitrin"),
    path("urunler/<slug:kategori>/", views.vitrin, name="vitrin_kategori"),
    path("urun/<slug:slug>/", views.urun, name="urun"),
]
