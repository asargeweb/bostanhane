from django.urls import path

from . import views

urlpatterns = [
    path("kurye/", views.bugun, name="kurye"),
    path("kurye/rota/<int:pk>/", views.rota, name="kurye_rota"),
    path("kurye/rota/<int:pk>/yola-cik/", views.yola_cik, name="kurye_yola_cik"),
    path("kurye/teslim/<str:numara>/", views.teslim, name="kurye_teslim"),
    path("kurye/teslim/<str:numara>/teslim-et/", views.teslim_et, name="kurye_teslim_et"),
    path("kurye/teslim/<str:numara>/ulasilamadi/", views.ulasilamadi, name="kurye_ulasilamadi"),
]
