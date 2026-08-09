
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from Taxis.models import Chofer
from Taxis.permissions import EsChofer
from Taxis.authentication import PerfilUsuarioJWTAuthentication

GRUPO_COLECTIVOS = "central_taxis_colectivos"


def _chofer_a_dict(chofer: Chofer) -> dict:
    return {
        "chofer_id": chofer.id,
        "nombre": f"{chofer.perfil.nombre or ''} {chofer.perfil.apellido or ''}".strip(),
        "vehiculo": f"{chofer.vehiculo.marca} {chofer.vehiculo.modelo}" if chofer.vehiculo else "Vehículo",
        "sketchfab_id": chofer.vehiculo.sketchfab_model_id if chofer.vehiculo else "",
        "asientos_disponibles": chofer.asientos_disponibles,
        "lat": float(chofer.latitud) if chofer.latitud else 0.0,
        "lng": float(chofer.longitud) if chofer.longitud else 0.0,
        "estado": chofer.get_estado_display(),
    }


class CambiarModalidadChoferView(APIView):
    authentication_classes = [PerfilUsuarioJWTAuthentication]
    permission_classes = [IsAuthenticated, EsChofer]

    def post(self, request):
        nuevo_estado = request.data.get("estado")
        if not nuevo_estado:
            return Response(
                {"status": "error", "message": "Falta el parámetro 'estado'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        chofer = getattr(request.user, "chofer_datos", None)
        if not chofer:
            return Response(
                {"status": "error", "message": "El usuario no tiene perfil de chofer."},
                status=status.HTTP_403_FORBIDDEN,
            )

        estados_validos = dict(Chofer.ESTADOS)
        if nuevo_estado not in estados_validos:
            return Response(
                {"status": "error", "message": "Estado inválido."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        chofer.estado = nuevo_estado
        chofer.save()

        channel_layer = get_channel_layer()

        if nuevo_estado in ("activo", "en_ruta"):
            # Iniciar turno -- avisa a React para que agregue el icono.
            async_to_sync(channel_layer.group_send)(
                GRUPO_COLECTIVOS,
                {
                    "type": "broadcast_chofer_conectado",
                    **_chofer_a_dict(chofer),
                },
            )
        elif nuevo_estado == "inactivo":
            # Finalizar turno -- avisa a React para que quite el icono.
            async_to_sync(channel_layer.group_send)(
                GRUPO_COLECTIVOS,
                {
                    "type": "broadcast_chofer_desconectado",
                    "chofer_id": chofer.id,
                },
            )

        return Response(
            {"status": "ok", "nuevo_estado": chofer.estado},
            status=status.HTTP_200_OK,
        )


class ActualizarUbicacionView(APIView):
    authentication_classes = [PerfilUsuarioJWTAuthentication]
    permission_classes = [IsAuthenticated, EsChofer]

    def post(self, request):
        lat = request.data.get("lat") or request.data.get("latitud")
        lng = request.data.get("lng") or request.data.get("longitud")

        if lat is None or lng is None:
            return Response(
                {"status": "error", "message": "Faltan coordenadas."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        chofer = getattr(request.user, "chofer_datos", None)
        if not chofer:
            return Response(
                {"status": "error", "message": "El usuario no tiene perfil de chofer."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if chofer.estado in ["pendiente", "inactivo"]:
            return Response(
                {"status": "error", "message": "Chofer no autorizado o inactivo."},
                status=status.HTTP_403_FORBIDDEN,
            )

        chofer.latitud = float(lat)
        chofer.longitud = float(lng)
        chofer.save()

        # Sin esto, React nunca se entera de la nueva posicion -- solo
        # quedaba guardada en la base de datos.
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            GRUPO_COLECTIVOS,
            {
                "type": "broadcast_ubicacion_actualizada",
                **_chofer_a_dict(chofer),
            },
        )

        return Response({"status": "ok"}, status=status.HTTP_200_OK)