"""
Plantilla de migración: api_cambiar_modalidad_chofer → CambiarModalidadChoferView.

AHORA:
    - El chofer se identifica por el token JWT (request.user).
    - Un chofer solo puede cambiar SU PROPIO estado.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from Taxis.models import Chofer
from Taxis.permissions import EsChofer


class CambiarModalidadChoferView(APIView):
    # AL DEFINIR ESTO AQUÍ, IGNORA 'SessionAuthentication' DE LA CONFIGURACIÓN GLOBAL
    # Únicamente valida el token Bearer JWT enviado desde Android
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, EsChofer]

    def post(self, request):
        nuevo_estado = request.data.get("estado")
        if not nuevo_estado:
            return Response(
                {"status": "error", "message": "Falta el parámetro 'estado'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not hasattr(request.user, "chofer_datos"):
            return Response(
                {"status": "error", "message": "Este usuario no tiene perfil de chofer."},
                status=status.HTTP_403_FORBIDDEN,
            )

        chofer = request.user.chofer_datos
        chofer.estado = nuevo_estado
        chofer.save()

        # Si el chofer apaga el turno, emitir la desconexión a React vía WebSocket
        if nuevo_estado == 'inactivo':
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                "central_taxis_colectivos",
                {
                    "type": "broadcast_chofer_desconectado",
                    "chofer_id": chofer.id
                }
            )

        return Response(
            {
                "status": "ok",
                "nuevo_estado": chofer.estado,
                "message": f"Estado actualizado a: {chofer.estado}",
            },
            status=status.HTTP_200_OK,
        )


class ActualizarUbicacionView(APIView):
    # AL DEFINIR ESTO AQUÍ, IGNORA 'SessionAuthentication' DE LA CONFIGURACIÓN GLOBAL
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, EsChofer]

    def post(self, request):
        lat = request.data.get("lat") or request.data.get("latitud")
        lng = request.data.get("lng") or request.data.get("longitud")

        if not lat or not lng:
            return Response(
                {"status": "error", "message": "Coordenadas incompletas."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not hasattr(request.user, "chofer_datos"):
            return Response(
                {"status": "error", "message": "Usuario sin perfil de chofer."},
                status=status.HTTP_403_FORBIDDEN,
            )

        chofer = request.user.chofer_datos
        chofer.latitud = float(lat)
        chofer.longitud = float(lng)
        chofer.save()

        return Response({"status": "ok"}, status=status.HTTP_200_OK)


class PagarRolView(APIView):
    permission_classes = [IsAuthenticated, EsChofer]

    def post(self, request):
        return Response(
            {"status": "ok", "message": "Rol pagado correctamente."},
            status=status.HTTP_200_OK,
        )