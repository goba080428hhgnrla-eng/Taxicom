"""
Ubicacion: Taxis/Taxis/authentication.py

Autenticacion JWT para TAXICOM. PerfilUsuario NO es el AUTH_USER_MODEL de
Django, asi que JWTAuthentication no puede resolver el usuario por defecto.
Esta clase busca directamente en PerfilUsuario usando id_usuario como PK.

Requiere en settings (Taxicom/settings/base.py):
    SIMPLE_JWT = {
        "USER_ID_FIELD": "id_usuario",
        "USER_ID_CLAIM": "user_id",
        ...
    }
"""
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, AuthenticationFailed
from rest_framework_simplejwt.settings import api_settings

from .models import PerfilUsuario


class PerfilUsuarioJWTAuthentication(JWTAuthentication):
    """Autentica el request y deja una instancia de PerfilUsuario en request.user."""

    def get_user(self, validated_token):
        try:
            user_id = validated_token[api_settings.USER_ID_CLAIM]
        except KeyError:
            raise InvalidToken("El token no contiene un identificador de usuario.")

        try:
            usuario = PerfilUsuario.objects.get(id_usuario=user_id)
        except PerfilUsuario.DoesNotExist:
            raise AuthenticationFailed("Usuario no encontrado.", code="user_not_found")

        return usuario