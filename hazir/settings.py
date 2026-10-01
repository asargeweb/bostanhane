"""
Bostanhane — Django ayarları

Bu dosya, `django-admin startproject bostanhane .` komutunun oluşturduğu
bostanhane/settings.py dosyasının yerine geçer.

Buradaki mantık: şifreler ve anahtarlar kodun içinde durmaz, .env dosyasından okunur.
Böylece kodu git'e gönderdiğinizde şifreleriniz dışarı sızmaz.
"""

from pathlib import Path
import os
from dotenv import load_dotenv

# Proje kök klasörü (manage.py'nin bulunduğu yer)
BASE_DIR = Path(__file__).resolve().parent.parent

# .env dosyasını oku
load_dotenv(BASE_DIR / ".env")


def ayar(anahtar, varsayilan=None):
    """Ortam değişkenini okur, yoksa varsayılanı döner."""
    return os.environ.get(anahtar, varsayilan)


# --------------------------------------------------------------------------
# Temel
# --------------------------------------------------------------------------
SECRET_KEY = ayar("DJANGO_SECRET_KEY", "gelistirme-icin-gecici-anahtar")
DEBUG = ayar("DJANGO_DEBUG", "True") == "True"
ALLOWED_HOSTS = [h.strip() for h in ayar("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost").split(",") if h.strip()]

# Railway her dağıtımda geçici bir adres verir; onu da listeye ekle
RAILWAY_ADRES = ayar("RAILWAY_PUBLIC_DOMAIN")
if RAILWAY_ADRES:
    ALLOWED_HOSTS.append(RAILWAY_ADRES)

# Form gönderiminde tarayıcı bu listeyi kontrol eder
CSRF_TRUSTED_ORIGINS = [f"https://{a}" for a in ALLOWED_HOSTS if a not in ("127.0.0.1", "localhost")]

# Canlıda (DEBUG kapalıyken) güvenlik ayarları
if not DEBUG:
    SECURE_SSL_REDIRECT = True                 # http ile gelen https'e yönlenir
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_HSTS_SECONDS = 3600
    X_FRAME_OPTIONS = "DENY"

# --------------------------------------------------------------------------
# Uygulamalar
# --------------------------------------------------------------------------
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

UCUNCU_PARTI_APPS = [
    "rest_framework",
    "storages",          # nesne depolama (R2 / B2 / S3) — aşağıdaki Medya bölümü
]

# Bostanhane uygulamaları — yeni modül ekledikçe buraya eklenecek
BOSTANHANE_APPS = [
    "core",
    "hesaplar",
    "katalog",
]

INSTALLED_APPS = DJANGO_APPS + UCUNCU_PARTI_APPS + BOSTANHANE_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "bostanhane.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "bostanhane.wsgi.application"

# --------------------------------------------------------------------------
# Veritabanı
#
# .env dosyasındaki DB_MOTOR değeri neyse o kullanılır:
#   sqlite   → tek dosyalık veritabanı, kurulum gerektirmez (başlangıç için)
#   postgres → PostgreSQL (canlı ortamda bunu kullanacağız)
#
# Şu an sqlite ile başlıyoruz. PostgreSQL kurulunca .env'de tek satır
# değiştirip geçeceğiz; kodun geri kalanı aynı kalır.
# --------------------------------------------------------------------------
DB_MOTOR = ayar("DB_MOTOR", "sqlite").lower()
DATABASE_URL = ayar("DATABASE_URL")

if DATABASE_URL:
    # Railway gibi servisler bağlantıyı tek bir adres olarak verir.
    import dj_database_url
    DATABASES = {"default": dj_database_url.parse(DATABASE_URL, conn_max_age=600)}
elif DB_MOTOR == "postgres":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": ayar("DB_NAME", "bostanhane"),
            "USER": ayar("DB_USER", "postgres"),
            "PASSWORD": ayar("DB_PASSWORD", ""),
            "HOST": ayar("DB_HOST", "127.0.0.1"),
            "PORT": ayar("DB_PORT", "5432"),
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "bostanhane.sqlite3",
        }
    }

# --------------------------------------------------------------------------
# Kullanıcı modeli
#
# Django'nun hazır kullanıcı tablosu yerine kendi modelimizi kullanıyoruz:
# giriş anahtarı kullanıcı adı değil **telefon numarası**.
#
# Bu satır projenin en başında konur. Sonradan değiştirmek veritabanının
# sıfırlanmasını gerektirir, çünkü bütün yetki tabloları buna bağlanır.
# --------------------------------------------------------------------------
AUTH_USER_MODEL = "hesaplar.Kullanici"

# Giriş sayfası henüz yazılmadı; şimdilik yönetim panelinin girişi kullanılıyor.
LOGIN_URL = "/yonetim/login/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"

# --------------------------------------------------------------------------
# Parola kuralları
# --------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# --------------------------------------------------------------------------
# Dil ve saat
# --------------------------------------------------------------------------
LANGUAGE_CODE = "tr"
TIME_ZONE = "Europe/Istanbul"
USE_I18N = True
USE_TZ = True

# --------------------------------------------------------------------------
# Statik dosyalar ve medya (ürün görselleri)
# --------------------------------------------------------------------------
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}

# --------------------------------------------------------------------------
# Medya (ürün ve kategori görselleri) — nesne depolama
#
# Yüklenen dosyalar sunucu diskine YAZILMAZ. Sebebi iki tane:
#   1. Railway'in dosya sistemi kalıcı değil; sonraki dağıtımda dosya silinir.
#   2. Kalıcı disk kiralasak bile Hobby planında 5 GB sınırı var ve bu sert sınır.
#
# Bu yüzden görseller S3 uyumlu bir nesne depolamaya gider. R2, Backblaze B2 ve
# AWS S3 aynı protokolü konuşur; hangisini kullandığınız yalnızca `S3_ENDPOINT_URL`
# ve `S3_REGION` değerlerini değiştirir, kod aynı kalır.
#
# Anahtarlar tanımlı değilse yerel diske düşer — bilgisayarda çalışırken hiçbir
# kurulum gerekmesin diye. Canlıda tanımsızsa `manage.py check` uyarı verir.
# --------------------------------------------------------------------------
S3_ACCESS_KEY_ID = ayar("S3_ACCESS_KEY_ID")
S3_SECRET_ACCESS_KEY = ayar("S3_SECRET_ACCESS_KEY")
S3_BUCKET = ayar("S3_BUCKET")
S3_ENDPOINT_URL = ayar("S3_ENDPOINT_URL")      # R2/B2 için şart, AWS S3'te boş
S3_REGION = ayar("S3_REGION", "auto")          # R2: auto · AWS: eu-central-1 gibi
S3_PUBLIC_URL = ayar("S3_PUBLIC_URL")          # görsellerin servis edileceği adres
S3_KLASOR = ayar("S3_KLASOR", "bostanhane/medya")

NESNE_DEPOLAMA_VAR = bool(S3_ACCESS_KEY_ID and S3_SECRET_ACCESS_KEY and S3_BUCKET)

if NESNE_DEPOLAMA_VAR:
    # custom_domain şema almaz: "https://cdn.bostanhane.com" değil "cdn.bostanhane.com"
    _acik_adres = (S3_PUBLIC_URL or "").strip().rstrip("/")
    for _on in ("https://", "http://"):
        if _acik_adres.startswith(_on):
            _acik_adres = _acik_adres[len(_on):]

    STORAGES["default"] = {
        "BACKEND": "storages.backends.s3.S3Storage",
        "OPTIONS": {
            "bucket_name": S3_BUCKET,
            "access_key": S3_ACCESS_KEY_ID,
            "secret_key": S3_SECRET_ACCESS_KEY,
            "endpoint_url": S3_ENDPOINT_URL or None,
            "region_name": S3_REGION,
            "signature_version": "s3v4",
            "location": S3_KLASOR,
            # R2 ve B2 ACL desteklemez; kova erişimi sağlayıcı panelinden ayarlanır.
            "default_acl": None,
            # Aynı adlı dosya yüklenirse eskisinin üzerine yazmasın.
            "file_overwrite": False,
            # Açık adres verildiyse düz URL kullan; verilmediyse imzalı (süreli)
            # URL üret — kova herkese açık olmasa da görseller panelde görünür.
            "custom_domain": _acik_adres or None,
            "querystring_auth": not bool(_acik_adres),
            "querystring_expire": 3600,
        },
    }
    MEDIA_URL = f"https://{_acik_adres}/{S3_KLASOR}/" if _acik_adres else "medya/"
else:
    MEDIA_URL = "medya/"

MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --------------------------------------------------------------------------
# Bostanhane iş kuralları
#
# Hepsi .env dosyasından okunur. Sebebi: bunlar iş kararı, kod değil.
# Teslimat ücretini değiştirmek için kodu düzeltip yeniden dağıtmak gerekmesin —
# Railway'de değişkeni değiştirip servisi yeniden başlatmak yeter.
#
# İleride yönetim panelinden mağaza bazında değiştirilebilir hale gelecek
# (Karaman'ın teslimat ücreti Beyşehir'den farklı olabilir).
# --------------------------------------------------------------------------
def sayi_ayar(anahtar, varsayilan):
    """Ortam değişkenini sayıya çevirir. Bozuk değer varsa varsayılana döner."""
    try:
        return float(ayar(anahtar, varsayilan))
    except (TypeError, ValueError):
        return float(varsayilan)


BOSTANHANE = {
    # Haftalık pazar alışverişine göre belirlendi: butik manav tek seferde
    # dolu sepet satar, kurye başına durak sayısı azalır, rota kendini çıkarır.
    "MIN_SEPET_TUTARI": sayi_ayar("MIN_SEPET_TUTARI", 500),            # TL
    "TESLIMAT_UCRETI": sayi_ayar("TESLIMAT_UCRETI", 50),               # TL
    "UCRETSIZ_TESLIMAT_ESIGI": sayi_ayar("UCRETSIZ_TESLIMAT_ESIGI", 1000),  # TL
    "PROVIZYON_TAMPON_ORANI": sayi_ayar("PROVIZYON_TAMPON_ORANI", 0.15),    # %15
    "OTOMATIK_TESLIM_ONAYI_SAAT": int(sayi_ayar("OTOMATIK_TESLIM_ONAYI_SAAT", 24)),
    "TALEP_ACMA_SURESI_SAAT": int(sayi_ayar("TALEP_ACMA_SURESI_SAAT", 24)),
}
