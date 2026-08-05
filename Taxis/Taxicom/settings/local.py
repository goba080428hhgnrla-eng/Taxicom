import os

from .base import *

# =========================================================
# GENERAL
# =========================================================

DEBUG = True

ALLOWED_HOSTS = [
    "*",
    "127.0.0.1",
    "localhost",
    ".onrender.com",
    "ritalin-detonator-womb.ngrok-free.dev",
]

CORS_ALLOW_ALL_ORIGINS = True

# =========================================================
# BASE DE DATOS (SUPABASE)
# =========================================================

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DB_NAME"),
        "USER": os.getenv("DB_USER"),
        "PASSWORD": os.getenv("DB_PASSWORD"),
        "HOST": os.getenv("DB_HOST"),
        "PORT": os.getenv("DB_PORT", "5432"),
        "CONN_MAX_AGE": 600,
        "OPTIONS": {
            "sslmode": "require",
        },
    }
}

# =========================================================
# SUPABASE STORAGE
# =========================================================

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET")

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
    os.path.join(BASE_DIR, 'Taxis', 'static'), 
]

# Usamos el almacenamiento recomendado sin romper builds si falta un manifest
STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'

MEDIA_URL = "/media/"

STORAGES = {
    "default": {
        "BACKEND": "Taxis.storage_backends.SupabaseStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    },
}
# =========================================================
# SEGURIDAD
# =========================================================

CSRF_TRUSTED_ORIGINS = [
    "https://ritalin-detonator-womb.ngrok-free.dev",
    "https://*.onrender.com",
]

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")