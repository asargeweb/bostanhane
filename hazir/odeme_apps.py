"""
Bostanhane — ödeme uygulaması tanımı

Bu dosya `odeme/apps.py` olarak kaydedilir.
"""

from django.apps import AppConfig


class OdemeConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "odeme"
    verbose_name = "Ödeme"
