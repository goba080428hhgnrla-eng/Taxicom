from .base import *
import boto3
import os
import time
from django.db.backends.postgresql.base import DatabaseWrapper

DEBUG = True

ALLOWED_HOSTS = [
    "*",
    "127.0.0.1",
    "localhost",
    ".onrender.com",
    "ritalin-detonator-womb.ngrok-free.dev",
]

CORS_ALLOW_ALL_ORIGINS = True

AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
REGION = "us-east-2"


# =========================================================
# AWS AURORA CONFIG (BASE DE DATOS)
# =========================================================
RDSHOST = "database-2.cluster-cbq2gaoyebpc.us-east-2.rds.amazonaws.com"
USER = "postgres"
DB_NAME = "postgres"
PORT = 5432 


# =========================================================
# VARIABLES GLOBALES PARA CACHÉ DE TOKEN IAM
# =========================================================
_CACHED_TOKEN = None
_TOKEN_GENERATED_AT = 0
TOKEN_DURATION_SECONDS = 600  


# =========================================================
# IAM TOKEN GENERATOR (OPTIMIZADO)
# =========================================================
def get_aws_token():
    """
    Genera y almacena en caché el token IAM para Aurora PostgreSQL.
    Evita que las peticiones constantes del monitor de uptime rompan
    la autenticación por exceso de tokens concurrentes.
    """
    global _CACHED_TOKEN, _TOKEN_GENERATED_AT
    
    current_time = time.time()
    
    # Si el token existe y tiene menos de 10 minutos, lo reutilizamos
    if _CACHED_TOKEN and (current_time - _TOKEN_GENERATED_AT) < TOKEN_DURATION_SECONDS:
        return _CACHED_TOKEN

    try:
        if not AWS_ACCESS_KEY_ID or not AWS_SECRET_ACCESS_KEY:
            raise Exception("Faltan credenciales AWS en variables de entorno")

        client = boto3.client(
            "rds",
            region_name=REGION,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        )

        # Generar un token nuevo de AWS
        nuevo_token = client.generate_db_auth_token(
            DBHostname=RDSHOST,
            Port=PORT,
            DBUsername=USER,
            Region=REGION,
        )
        
        # Guardar en la caché global con la marca de tiempo actual
        _CACHED_TOKEN = nuevo_token
        _TOKEN_GENERATED_AT = current_time
        
        print("--- [INFO] NUEVO TOKEN IAM GENERADO CORRECTAMENTE ---")
        return _CACHED_TOKEN

    except Exception as e:
        print("IAM TOKEN ERROR:", e)
        # Si falla AWS por red, devolvemos el último token conocido como salvavidas
        if _CACHED_TOKEN:
            return _CACHED_TOKEN
        return ""


# =========================================================
# DATABASE CONFIG
# =========================================================
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": DB_NAME,
        "USER": USER,
        "HOST": RDSHOST,
        "PORT": str(PORT),
        "OPTIONS": {
            "sslmode": "require",
        },
    }
}


# =========================================================
# PARCHE EN CALIENTE (MONKEY PATCH) PARA EXTENDER EL MOTOR
# =========================================================
# Guardamos la referencia del método nativo de Django
_original_get_new_connection = DatabaseWrapper.get_new_connection

def _iam_get_new_connection(self, conn_params):
    """
    Intercepta el intento de conexión física e inyecta el token dinámico
    en las credenciales justo antes de abrir el socket con Aurora.
    """
    conn_params['password'] = get_aws_token()
    return _original_get_new_connection(self, conn_params)

# Inyectamos nuestro comportamiento en el conector de Django
DatabaseWrapper.get_new_connection = _iam_get_new_connection


# =========================================================
# CONFIGURACIÓN DE ARCHIVOS ESTÁTICOS ( WhiteNoise )
# =========================================================
STATIC_URL = '/static/'

STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

STATIC_ROOT = BASE_DIR / 'staticfiles'

STATICFILES_STORAGE = (
    'whitenoise.storage.CompressedManifestStaticFilesStorage'
)


# =========================================================
# CONFIGURACIÓN DE ARCHIVOS MULTIMEDIA ( Amazon S3 )
# =========================================================
AWS_STORAGE_BUCKET_NAME = "agroconecta-media"
AWS_S3_REGION_NAME = REGION

# Parámetros obligatorios para la autenticación y permisos
AWS_QUERYSTRING_AUTH = False  # Evita firmas dinámicas temporales
AWS_S3_FILE_OVERWRITE = False # No sobrescribe fotos con el mismo nombre

# Configuración moderna para Django 4.2+ (OBLIGATORIA)
STORAGES = {
    "default": {
        "BACKEND": "storages.backends.s3.S3Storage",  # Indica que los archivos de usuario van a S3
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage", # Para tus CSS/JS locales
    },
}

# Generación dinámica del dominio público para acceder a las imágenes
AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/'


# =========================================================
# CSRF (FIX IMPORTANTE)
# =========================================================
CSRF_TRUSTED_ORIGINS = [
    "https://ritalin-detonator-womb.ngrok-free.dev",
    "https://*.onrender.com",
]


# =========================================================
# SECURITY (Render)
# =========================================================
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")