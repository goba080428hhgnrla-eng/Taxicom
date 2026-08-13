from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import (
    InvalidToken,
    AuthenticationFailed
)
from rest_framework_simplejwt.settings import api_settings

from .models import PerfilUsuario


class PerfilUsuarioJWTAuthentication(
    JWTAuthentication
):

    def get_user(
        self,
        validated_token
    ):

        try:

            user_id = validated_token[
                api_settings.USER_ID_CLAIM
            ]

        except KeyError:

            raise InvalidToken(
                "El token no contiene "
                "un identificador de usuario."
            )

        try:

            usuario = (
                PerfilUsuario.objects.get(
                    id_usuario=user_id
                )
            )

        except PerfilUsuario.DoesNotExist:

            raise AuthenticationFailed(
                "Usuario no encontrado.",
                code="user_not_found"
            )

        return usuario