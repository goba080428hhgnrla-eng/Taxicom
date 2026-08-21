"""
Ubicacion: Taxis/Taxis/api/v1/choferes.py
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
    """Shape idéntico al handler broadcast_ubicacion en consumers.py."""
    nombre_completo = "Chofer"
    if hasattr(chofer, 'perfil') and chofer.perfil:
        nombre_completo = f"{chofer.perfil.nombre or ''} {chofer.perfil.apellido or ''}".strip()
    elif hasattr(chofer, 'usuario') and chofer.usuario:
        nombre_completo = f"{getattr(chofer.usuario, 'nombre', '')} {getattr(chofer.usuario, 'apellido', '')}".strip()

    vehiculo_str = "Vehículo"
    if getattr(chofer, 'vehiculo', None):
        vehiculo_str = f"{chofer.vehiculo.marca} {chofer.vehiculo.modelo}"

    return {
        "type": "broadcast_ubicacion",
        "chofer_id": chofer.id,
        "latitud": chofer.latitud or 0.0,
        "longitud": chofer.longitud or 0.0,
        "nombre": nombre_completo or "Chofer Activo",
        "vehiculo": vehiculo_str,
        "modalidad": chofer.get_estado_display() if hasattr(chofer, 'get_estado_display') else chofer.estado,
        "asientos_disponibles": getattr(chofer, 'asientos_disponibles', 0),
    }


class CambiarModalidadChoferView(APIView):

    authentication_classes = [
        PerfilUsuarioJWTAuthentication
    ]

    permission_classes = [
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

        chofer = getattr(request.user, "chofer_datos", None)

        if not chofer:
            return Response(
                {
                    "status": "error",
                    "message": "El usuario no tiene perfil de chofer."
                },
                status=status.HTTP_403_FORBIDDEN
            )

        estados_validos = dict(Chofer.ESTADOS)

        if nuevo_estado not in estados_validos:
            return Response(
                {
                    "status": "error",
                    "message": "Estado inválido.",
                    "estados_validos": list(estados_validos.keys())
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        chofer.estado = nuevo_estado
        chofer.save(update_fields=["estado"])

        # =====================================================
        # SI EL CHOFER ESTÁ ACTIVO O EN RUTA
        # =====================================================
        if nuevo_estado in ("activo", "en_ruta"):
            try:
                channel_layer = get_channel_layer()
                payload = _payload_ubicacion(chofer)
                async_to_sync(channel_layer.group_send)(
                    GRUPO_COLECTIVOS,
                    payload
                )
            except Exception as e:
                print(f"Error enviando broadcast de ubicación: {e}")

        # =====================================================
        # SI SE DESACTIVA
        # =====================================================
        elif nuevo_estado == "inactivo":
            try:
                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    GRUPO_COLECTIVOS,
                    {
                        "type": "broadcast_chofer_desconectado",
                        "chofer_id": chofer.id
                    }
                )
            except Exception as e:
                print(f"Error enviando broadcast de desconexión: {e}")

        return Response(
            {
                "status": "ok",
                "nuevo_estado": chofer.estado
            },
            status=status.HTTP_200_OK
        )


class ActualizarUbicacionSerializer(serializers.Serializer):
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

        # Propagar la ubicación en tiempo real
        try:
            channel_layer = get_channel_layer()
            payload = _payload_ubicacion(chofer)
            async_to_sync(channel_layer.group_send)(
                GRUPO_COLECTIVOS,
                payload
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
        
        if PagoRol.objects.filter(chofer=chofer, fecha_pago__date=hoy, estado__in=["pagado", "pendiente"]).exists():
            return Response(
                {"status": "error", "message": "Ya tienes un pago registrado o pendiente para el día de hoy."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        PagoRol.objects.create(
            chofer=chofer,
            monto=serializer.validated_data["monto"],
            estado='pendiente',
            fecha_pago=timezone.now()
        )

        return Response(
            {"status": "ok", "message": "Solicitud de pago enviada. Esperando confirmación del administrador."},
            status=status.HTTP_200_OK,
        )