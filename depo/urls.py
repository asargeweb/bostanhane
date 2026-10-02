from django.urls import path

from . import alim as alim_gorunumleri
from . import views

urlpatterns = [
    path("depo/", views.gunler, name="depo"),
    path("depo/gun/<int:pk>/", views.gun, name="depo_gun"),
    path("depo/gun/<int:pk>/kes/", views.gunu_kes_view, name="depo_gunu_kes"),
    path("depo/toplama/<str:numara>/", views.toplama, name="depo_toplama"),
    path("depo/toplama/<str:numara>/kalem/<int:pk>/", views.tartim, name="depo_tartim"),
    path("depo/toplama/<str:numara>/hazir/", views.hazir, name="depo_hazir"),
    # Alım listesi (Cowork): hale günde bir kez gidilir, liste tarihe bağlı.
    path("depo/alim/<str:tarih>/", alim_gorunumleri.alim, name="depo_alim"),
    path("depo/alim/takvim/<int:pk>/", alim_gorunumleri.alim_takvimden, name="depo_alim_takvim"),
]
