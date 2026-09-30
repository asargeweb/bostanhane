"""
Bostanhane — hesaplar uygulaması tanımı

Bu dosya `hesaplar/apps.py` yerine geçer.
`verbose_name` yönetim panelinin ana sayfasındaki bölüm başlığıdır.
"""

from django.apps import AppConfig


class HesaplarConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "hesaplar"
    verbose_name = "Hesaplar"
