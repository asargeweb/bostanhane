from django.apps import AppConfig


class DepoConfig(AppConfig):
    """
    Depo ekranları: paketleme elemanının tabletten kullandığı sade sayfalar.
    Kendi modeli yok; sipariş ve katalog modellerini kullanır. Paketleme
    elemanı yönetim paneline girmez, bu ekranlar normal site sayfasıdır.
    """
    default_auto_field = "django.db.models.BigAutoField"
    name = "depo"
    verbose_name = "Depo"
