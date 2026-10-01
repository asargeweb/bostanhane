"""
Bostanhane — katalog uygulaması tanımı

Bu dosya `katalog/apps.py` yerine geçer.
"""

from django.apps import AppConfig


class KatalogConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "katalog"
    verbose_name = "Katalog"
