"""
Ubicacion: Taxis/Taxis/api/v1/choferes.py

Ultima correccion: los broadcasts ahora reutilizan el handler
"broadcast_ubicacion" que YA existe en consumers.py -- ya no se inventa un
"broadcast_chofer_conectado" que no tiene handler (eso era lo que tumbaba
el WebSocket). Los nombres de campo (latitud/longitud, no lat/lng) tienen
que coincidir EXACTO con lo que consumers.py lee via event["latitud"], etc,
o vuelve a tronar con KeyError en vez de ValueError, pero igual tumba la
conexion.
"""
from django.utils import timezone
from rest_framework import serializers, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from Taxis.models import Chofer, PagoRol
from Taxis.permissions import EsChofer
from Taxis.authentication import PerfilUsuarioJWTAuthentication

GRUPO_COLECTIVOS = "central_taxis_colectivos"


def _payload_ubicacion(chofer: Chofer) -> dict:
    """Mismo shape que espera el handler broadcast_ubicacion en consumers.py."""
    return {
        "type": "broadcast_ubicacion",
        "chofer_id": chofer.id,
        "latitud": chofer.latitud,
        "longitud": chofer.longitud,
        "nombre": f"{chofer.perfil.nombre or ''} {chofer.perfil.apellido or ''}".strip(),
        "vehiculo": f"{chofer.vehiculo.marca} {chofer.vehiculo.modelo}" if chofer.vehiculo else "Vehículo",
        "modalidad": chofer.get_estado_display(),
        "asientos_disponibles": chofer.asientos_disponibles,
    }


class CambiarModalidadChoferView(APIView):

    authentication_classes = [
        PerfilUsuarioJWTAuthentication
    ]

    permission_classes = [
        IsAuthenticated,
        EsChofer
    ]

    def post(self, request):

        nuevo_estado = request.data.get("estado")

        if not nuevo_estado:

            return Response(
                {
                    "status": "error",
                    "message": "Falta el parámetro 'estado'."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        chofer = getattr(
            request.user,
            "chofer_datos",
            None
        )

        if not chofer:

            return Response(
                {
                    "status": "error",
                    "message": (
                        "El usuario no tiene perfil de chofer."
                    )
                },
                status=status.HTTP_403_FORBIDDEN
            )

        estados_validos = dict(
            Chofer.ESTADOS
        )

        if nuevo_estado not in estados_validos:

            return Response(
                {
                    "status": "error",
                    "message": "Estado inválido.",
                    "estados_validos": list(
                        estados_validos.keys()
                    )
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        chofer.estado = nuevo_estado
        chofer.save(
            update_fields=["estado"]
        )

        channel_layer = get_channel_layer()

        if nuevo_estado in (
            "activo",
            "en_ruta"
        ):

            async_to_sync(
                channel_layer.group_send
            )(
                GRUPO_COLECTIVOS,
                _payload_ubicacion(chofer)
            )

        elif nuevo_estado == "inactivo":

            async_to_sync(
                channel_layer.group_send
            )(
                GRUPO_COLECTIVOS,
                {
                    "type":
                        "broadcast_chofer_desconectado",

                    "chofer_id":
                        chofer.id,
                }
            )

        return Response(
            {
                "status": "ok",
                "nuevo_estado": chofer.estado,
            },
            status=status.HTTP_200_OK
        )


class ActualizarUbicacionSerializer(
    serializers.Serializer
):

    lat = serializers.FloatField()

    lng = serializers.FloatField()


class ActualizarUbicacionView(APIView):

    authentication_classes = [
        PerfilUsuarioJWTAuthentication
    ]

    permission_classes = [
        IsAuthenticated,
        EsChofer
    ]

    def post(self, request):

        serializer = ActualizarUbicacionSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        chofer = getattr(
            request.user,
            "chofer_datos",
            None
        )

        if not chofer:

            return Response(
                {
                    "status": "error",
                    "message": (
                        "El usuario autenticado "
                        "no tiene perfil de chofer."
                    )
                },
                status=status.HTTP_403_FORBIDDEN
            )

        lat = serializer.validated_data["lat"]
        lng = serializer.validated_data["lng"]

        chofer.latitud = lat
        chofer.longitud = lng

        # Si tu modelo tiene este campo
        if hasattr(chofer, "ultima_actualizacion"):
            chofer.ultima_actualizacion = timezone.now()

            chofer.save(
                update_fields=[
                    "latitud",
                    "longitud",
                    "ultima_actualizacion"
                ]
            )

        else:

            chofer.save(
                update_fields=[
                    "latitud",
                    "longitud"
                ]
            )

        return Response(
            {
                "status": "ok",
                "message": "Ubicación actualizada.",
                "lat": lat,
                "lng": lng,
            },
            status=status.HTTP_200_OK
        )


class PagarRolSerializer(serializers.Serializer):
    monto = serializers.FloatField(min_value=0.01)


class PagarRolView(APIView):
    authentication_classes = [PerfilUsuarioJWTAuthentication]
    permission_classes = [IsAuthenticated, EsChofer]

    def post(self, request):
        serializer = PagarRolSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        chofer = getattr(request.user, "chofer_datos", None)
        if not chofer:
            return Response(
                {"status": "error", "message": "El usuario no tiene perfil de chofer."},
                status=status.HTTP_403_FORBIDDEN,
            )

        hoy = timezone.now().date()
        if PagoRol.objects.filter(chofer=chofer, fecha_pago__date=hoy, estado="pagado").exists():
            return Response(
                {"status": "error", "message": "El chofer ya pago el rol hoy."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        resultado = chofer.pagar_rol(serializer.validated_data["monto"])

        if resultado:
            return Response(
                {"status": "ok", "message": "Pago de rol realizado y chofer activado."},
                status=status.HTTP_200_OK,
            )
        return Response(
            {"status": "error", "message": "El chofer ya pago el rol hoy."},
            status=status.HTTP_400_BAD_REQUEST,
        )