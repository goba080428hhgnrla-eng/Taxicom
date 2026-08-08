"""
Plantilla de migración: api_cambiar_modalidad_chofer → CambiarModalidadChoferView.

AHORA:
    - El chofer se identifica por el token JWT (request.user).
    - Un chofer solo puede cambiar SU PROPIO estado.
"""
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

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

        # Si el chofer pasa a inactivo o apaga turno, notificar la desconexión a React
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
                {"status": "error", "message": "Faltan latitud o longitud."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        chofer = request.user.chofer_datos
        chofer.latitud = lat
        chofer.longitud = lng
        chofer.save()

        # Obtener nombre de forma segura evitando AttributeError
        first_name = getattr(request.user, 'first_name', None) or getattr(request.user, 'nombre', '')
        last_name = getattr(request.user, 'last_name', None) or getattr(request.user, 'apellido', '')
        nombre_completo = f"{first_name} {last_name}".strip() or f"Chofer #{chofer.id}"

        # Obtener datos del vehículo si existe
        info_vehiculo = f"{chofer.vehiculo.marca} {chofer.vehiculo.modelo}" if getattr(chofer, 'vehiculo', None) else "Taxi Colectivo"

        # Retransmitir en tiempo real a React a través del Channel Layer
        channel_layer = get_channel_layer()
        
        if chofer.estado == 'inactivo':
            # Si el chofer está inactivo, notificar la eliminación del vehículo
            async_to_sync(channel_layer.group_send)(
                "central_taxis_colectivos",
                {
                    "type": "broadcast_chofer_desconectado",
                    "chofer_id": chofer.id
                }
            )
        else:
            # Emitir actualización al mapa web
            async_to_sync(channel_layer.group_send)(
                "central_taxis_colectivos",
                {
                    "type": "broadcast_ubicacion",
                    "chofer_id": chofer.id,
                    "latitud": float(lat),
                    "longitud": float(lng),
                    "nombre": nombre_completo,
                    "vehiculo": info_vehiculo,
                    "modalidad": getattr(chofer, 'modalidad', 'COLECTIVO'),
                    "asientos_disponibles": getattr(chofer, 'asientos_disponibles', 4)
                }
            )

        return Response({"status": "ok"}, status=status.HTTP_200_OK)


class PagarRolView(APIView):
    permission_classes = [IsAuthenticated, EsChofer]

    def post(self, request):
        return Response(
            {"status": "ok", "message": "Rol pagado correctamente."},
            status=status.HTTP_200_OK,
        )