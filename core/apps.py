"""
Bostanhane — core uygulaması tanımı

Bu dosya `core/apps.py` yerine geçer.

Buradaki tek iş, bir **kontrol** (system check) eklemek: canlı ortamda nesne
depolama tanımlı değilse uyarı vermek.

Neden gerekli: Django hata vermeden görseli sunucu diskine yazar, ama Railway'in
diski kalıcı olmadığı için dosya bir sonraki dağıtımda silinir. Yani sessiz veri
kaybı. `manage.py check` her dağıtımda çalıştığı için uyarı dağıtım kayıtlarında
görünür ve gözden kaçmaz.
"""

from django.apps import AppConfig
from django.core.checks import Warning as KontrolUyarisi
from django.core.checks import register


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core"
    verbose_name = "Çekirdek"


@register()
def medya_depolama_kontrolu(app_configs, **kwargs):
    """Canlıda görseller nereye yazılıyor? Diske yazıyorsa uyar."""
    from django.conf import settings

    if settings.DEBUG:
        return []
    if getattr(settings, "NESNE_DEPOLAMA_VAR", False):
        return []
    return [
        KontrolUyarisi(
            "Yüklenen görseller sunucu diskine yazılıyor; bir sonraki dağıtımda silinecek.",
            hint="S3_ACCESS_KEY_ID, S3_SECRET_ACCESS_KEY ve S3_BUCKET ortam "
                 "değişkenlerini tanımlayın. Ayrıntı: adim-4b-gorsel-depolama.md",
            id="bostanhane.W001",
        )
    ]


@register()
def yasal_metin_kontrolu(app_configs, **kwargs):
    """
    Canlıda yasal metinlerde doldurulmamış `xxx` (şirket unvanı, vergi no, adres…)
    kaldıysa uyar. Şirket bilgileri olmadan sözleşme hükümsüz, KVKK aydınlatması
    eksik olur; bunu insan hafızasına bırakmıyoruz.
    """
    from pathlib import Path

    from django.conf import settings

    if settings.DEBUG:
        return []
    isaret = 'class="xxx"'
    klasor = Path(settings.BASE_DIR) / "templates" / "yasal"
    eksikler = []
    for dosya in sorted(klasor.glob("*.html")):
        adet = dosya.read_text(encoding="utf-8").count(isaret)
        if adet:
            eksikler.append(f"{dosya.name} ({adet})")
    if not eksikler:
        return []
    return [
        KontrolUyarisi(
            "Yasal metinlerde doldurulmamış şirket bilgisi (xxx) var: " + ", ".join(eksikler),
            hint="Unvan, vergi no, MERSİS ve adres girilmeden gerçek satışa geçilmemeli. "
                 "Dosyalar: templates/yasal/",
            id="bostanhane.W002",
        )
    ]
