import os
import django

# Configurar el entorno de Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Taxicom.settings.local")
django.setup()

from django.contrib.auth.models import User
from Taxis.models import PerfilUsuario

def inicializar_administrador():
    username = "admin_principal2"
    email = "admin2@taxicom.com"
    password = "12345678"
    
    # Verificar si el usuario ya existe para no duplicarlo
    if not User.objects.filter(username=username).exists():
        # create_superuser se encarga de encriptar la contraseña automáticamente
        user = User.objects.create_superuser(
            username=username,
            email=email,
            password=password,
            first_name="Administrador",
            last_name="General"
        )
        
        # Crear su perfil
        PerfilUsuario.objects.create(
            user=user,
            rol="admin",
            telefono="5599887766"
        )
        print(f"✅ Administrador '{username}' creado exitosamente.")
    else:
        print(f"⚠️ El usuario '{username}' ya existe en la base de datos.")

if __name__ == "__main__":
    inicializar_administrador()