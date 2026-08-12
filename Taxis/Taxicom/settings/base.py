import os
from pathlib import Path
from datetime import timedelta

"""
Django settings for agoconecta / Taxicom project.
"""

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent


print(f"DEBUG BASE_DIR: {BASE_DIR}")

SECRET_KEY = 'django-insecure-d(6h-umj3bkd9l&9*1-$z+m(i7-jhjlvsj*je%_&q+=u85zju^'

INSTALLED_APPS = [
    'daphne',
    'channels',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'Taxis',
    'storages',
    'bcrypt',
    "rest_framework_simplejwt",
]
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "Taxis.authentication.PerfilUsuarioJWTAuthentication",
    ),

    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
}


SIMPLE_JWT = {

    "USER_ID_FIELD": "id_usuario",

    "USER_ID_CLAIM": "user_id",

    # Access token
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=8),

    # Refresh token
    "REFRESH_TOKEN_LIFETIME": timedelta(days=14),

    # Renovación
    "ROTATE_REFRESH_TOKENS": True,

    "BLACKLIST_AFTER_ROTATION": False,

    # Formato
    "AUTH_HEADER_TYPES": ("Bearer",),

    # Errores
    "AUTH_TOKEN_CLASSES": (
        "rest_framework_simplejwt.tokens.AccessToken",
    ),

    "TOKEN_TYPE_CLAIM": "token_type",
}


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'Taxicom.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'templates',
            BASE_DIR / 'Taxis' / 'templates',
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

ASGI_APPLICATION = 'Taxicom.asgi.application'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'es-mx'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [{
                "address": os.environ.get("REDIS_URL"),
                "retry_on_timeout": True,
                "retry_on_error": [ConnectionError, TimeoutError],
                "health_check_interval": 5,
                "socket_keepalive": True,
                "socket_timeout": 60,
                "socket_connect_timeout": 60,
            }],
            "capacity": 2000,
            "expiry": 30,
            "group_expiry": 43200,
        },
    },
}