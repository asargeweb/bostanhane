from django.apps import AppConfig


class LojistikConfig(AppConfig):
    """
    Kurye ekranları: günün rotası ve teslim kaydı. Telefonda, tek elle kullanılır.
    Kendi modeli yok; sipariş modelini kullanır. Kurye yönetim paneline girmez.
    """
    default_auto_field = "django.db.models.BigAutoField"
    name = "lojistik"
    verbose_name = "Lojistik"
