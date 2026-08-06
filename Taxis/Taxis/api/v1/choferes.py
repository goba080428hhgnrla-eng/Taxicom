"""
Plantilla de migración: api_cambiar_modalidad_chofer → CambiarModalidadChoferView.

ANTES (api_views.py):
    - El request mandaba `usuario_id` en el body.
    - Cualquiera que supiera un usuario_id podía cambiar el estado de
      cualquier chofer, sin verificar que fuera ese chofer.

AHORA:
    - El chofer se identifica por el token JWT (request.user), no por un
      campo del body.
    - Un chofer solo puede cambiar SU PROPIO estado.
    - Repite este patrón (permission_classes = [IsAuthenticated, EsChofer]
      + usar request.user.chofer_datos en vez de un id del body) para migrar
      actualizar_ubicacion_chofer, api_pagar_rol y api_solicitar_viaje_especial.
"""
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from Taxis.models import Chofer
from Taxis.permissions import EsChofer


class CambiarModalidadChoferView(APIView):
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

        estados_validos = dict(Chofer.ESTADOS)
        if nuevo_estado not in estados_validos:
            return Response(
                {"status": "error", "message": "Estado inválido."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        chofer.estado = nuevo_estado
        chofer.save()

        return Response(
            {
                "status": "ok",
                "nuevo_estado": chofer.estado,
                "message": f"Estado actualizado a: {chofer.get_estado_display()}",
            },
            status=status.HTTP_200_OK,
        )
        
        
class ActualizarUbicacionView(APIView):
    permission_classes = [IsAuthenticated, EsChofer]

    def post(self, request):
        lat = request.data.get("latitud")
        lng = request.data.get("longitud")

        if lat is None or lng is None:
            return Response(
                {"status": "error", "message": "Faltan parámetros 'latitud' o 'longitud'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        chofer = request.user.chofer_datos
        chofer.latitud = lat
        chofer.longitud = lng
        chofer.save()

        return Response(
            {"status": "ok", "message": "Ubicación actualizada correctamente."},
            status=status.HTTP_200_OK,
        )


class PagarRolView(APIView):
    permission_classes = [IsAuthenticated, EsChofer]

    def post(self, request):
        # Implementación de tu lógica de pago de rol
        return Response(
            {"status": "ok", "message": "Rol pagado correctamente."},
            status=status.HTTP_200_OK,
        )        