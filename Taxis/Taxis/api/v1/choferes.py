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
        EsChofer
    ]

    def post(
        self,
        request
    ):

        nuevo_estado = request.data.get(
            "estado"
        )

        if not nuevo_estado:

            return Response(
                {
                    "status": "error",
                    "message":
                        "Falta el parámetro 'estado'."
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
                    "message":
                        "El usuario no tiene perfil de chofer."
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
                    "message":
                        "Estado inválido.",
                    "estados_validos":
                        list(
                            estados_validos.keys()
                        )
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        chofer.estado = nuevo_estado

        chofer.save(
            update_fields=[
                "estado"
            ]
        )

        # =====================================================
        # SI EL CHOFER ESTÁ ACTIVO
        # =====================================================

        if nuevo_estado in (
            "activo",
            "en_ruta"
        ):

            try:

                channel_layer = (
                    get_channel_layer()
                )

                async_to_sync(
                    channel_layer.group_send
                )(
                    GRUPO_COLECTIVOS,
                    {
                        "type":
                            "broadcast_ubicacion",

                        "chofer_id":
                            chofer.id,

                        "latitud":
                            chofer.latitud,

                        "longitud":
                            chofer.longitud,

                        "nombre":
                            getattr(
                                chofer.usuario,
                                "nombre",
                                "Chofer"
                            ),

                        "vehiculo":
                            "Vehículo Activo",

                        "modalidad":
                            nuevo_estado,

                        "asientos_disponibles":
                            getattr(
                                chofer,
                                "asientos_disponibles",
                                0
                            )
                    }
                )

            except Exception as e:

                print(
                    "Error enviando "
                    f"broadcast: {e}"
                )

        # =====================================================
        # SI SE DESACTIVA
        # =====================================================

        elif nuevo_estado == "inactivo":

            try:

                channel_layer = (
                    get_channel_layer()
                )

                async_to_sync(
                    channel_layer.group_send
                )(
                    GRUPO_COLECTIVOS,
                    {
                        "type":
                            "broadcast_chofer_desconectado",

                        "chofer_id":
                            chofer.id
                    }
                )

            except Exception as e:

                print(
                    "Error enviando "
                    f"desconexión: {e}"
                )

        return Response(
            {
                "status": "ok",
                "nuevo_estado":
                    chofer.estado
            },
            status=status.HTTP_200_OK
        )

class ActualizarUbicacionSerializer(
    serializers.Serializer
):

    lat = serializers.FloatField()

    lng = serializers.FloatField()


class ActualizarUbicacionView(APIView):

    authentication_classes = [PerfilUsuarioJWTAuthentication]
    permission_classes = [IsAuthenticated, EsChofer]

    def post(self, request):

        chofer = getattr(request.user, "chofer_datos", None)

        if not chofer:
            return Response(
                {"status": "error", "message": "El usuario no tiene perfil de chofer."},
                status=status.HTTP_403_FORBIDDEN
            )

        lat = request.data.get("lat")
        lng = request.data.get("lng")

        if lat is None or lng is None:
            return Response(
                {"status": "error", "message": "Se requieren lat y lng."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            chofer.latitud = float(lat)
            chofer.longitud = float(lng)
            chofer.save(update_fields=["latitud", "longitud"])
        except (ValueError, TypeError):
            return Response(
                {"status": "error", "message": "Coordenadas inválidas."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # NUEVO: propagar la ubicación en tiempo real
        try:
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                GRUPO_COLECTIVOS,
                {
                    "type": "broadcast_ubicacion",
                    "chofer_id": chofer.id,
                    "latitud": chofer.latitud,
                    "longitud": chofer.longitud,
                    "nombre": f"{chofer.perfil.nombre or ''} {chofer.perfil.apellido or ''}".strip(),
                    "vehiculo": f"{chofer.vehiculo.marca} {chofer.vehiculo.modelo}" if chofer.vehiculo else "Vehículo",
                    "modalidad": chofer.get_estado_display(),
                    "asientos_disponibles": chofer.asientos_disponibles,
                },
            )
        except Exception as e:
            print(f"Error enviando broadcast de ubicación: {e}")

        return Response(
            {"status": "ok", "lat": chofer.latitud, "lng": chofer.longitud},
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