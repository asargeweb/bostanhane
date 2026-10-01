from django.urls import path

from . import views

# /depo/alim/<takvim>/ (alım listesi) Cowork'ün ekranı; burada tanımlanmıyor.
urlpatterns = [
    path("depo/", views.gunler, name="depo"),
    path("depo/gun/<int:pk>/", views.gun, name="depo_gun"),
    path("depo/gun/<int:pk>/kes/", views.gunu_kes_view, name="depo_gunu_kes"),
    path("depo/toplama/<str:numara>/", views.toplama, name="depo_toplama"),
    path("depo/toplama/<str:numara>/kalem/<int:pk>/", views.tartim, name="depo_tartim"),
    path("depo/toplama/<str:numara>/hazir/", views.hazir, name="depo_hazir"),
]
