"""
Bostanhane — sipariş uygulaması tanımı

Bu dosya `siparis/apps.py` yerine geçer.

`verbose_name` panelin sol menüsünde görünen başlıktır; Django "Siparis" yazardı,
biz düzgün Türkçesini yazıyoruz.
"""

from django.apps import AppConfig


class SiparisConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "siparis"
    verbose_name = "Siparişler"
