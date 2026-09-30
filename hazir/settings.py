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
]

# Bostanhane uygulamaları — yeni modül ekledikçe buraya eklenecek
BOSTANHANE_APPS = [
    "core",
    "hesaplar",
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

MEDIA_URL = "medya/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --------------------------------------------------------------------------
# Bostanhane iş kuralları — varsayılanlar
# Bunlar ileride yönetim panelinden değiştirilebilir hale gelecek.
# --------------------------------------------------------------------------
BOSTANHANE = {
    "MIN_SEPET_TUTARI": 150,          # TL
    "TESLIMAT_UCRETI": 40,            # TL
    "UCRETSIZ_TESLIMAT_ESIGI": 300,   # TL
    "PROVIZYON_TAMPON_ORANI": 0.15,   # %15
    "OTOMATIK_TESLIM_ONAYI_SAAT": 24, # saat
    "TALEP_ACMA_SURESI_SAAT": 24,     # saat
}
