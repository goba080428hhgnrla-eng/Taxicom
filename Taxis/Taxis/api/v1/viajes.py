"""
Ubicacion: Taxis/Taxis/api/v1/viajes.py

Endpoints de viajes para el cliente (app Android).
Reemplazan api_solicitar_viaje_especial y api_crear_calificacion.

Nota sobre el original: api_solicitar_viaje_especial creaba instancias del
modelo Viaje (no ViajeEspecial), a pesar del nombre. Se respeta ese
comportamiento aqui para no romper lo que ya funciona; si en realidad
querias usar el modelo ViajeEspecial para esto, avisame y lo separamos.

Cambios de seguridad respecto al original:
- Ya no se manda cliente_id en el body: se usa request.user.
- api_crear_calificacion original NO verificaba que el viaje fuera del
  cliente que calificaba, ni que el viaje estuviera terminado -- cualquiera
  podia calificar cualquier viaje adivinando el id. Aqui si se valida.
"""
import math
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ...models import Viaje, Calificacion, Chofer
from ...permissions import EsCliente


def calcular_distancia(lat1, lon1, lat2, lon2):
    """Calcula la distancia aproximada en kilómetros entre dos puntos (Haversine)."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def asignar_colectivo_automatico(viaje: Viaje):
    # Buscamos choferes que estén en ruta o activos
    choferes_candidatos = Chofer.objects.filter(
        estado__in=['activo', 'en_ruta']
    ).select_related('vehiculo', 'perfil')

    candidatos_validos = []

    for chofer in choferes_candidatos:
        # 1. Validar asientos disponibles
        if chofer.asientos_disponibles < viaje.asientos_solicitados:
            continue
        
        # 2. Validar cajuela si el pasajero la requiere
        if viaje.requiere_cajuela:
            if not chofer.vehiculo or not chofer.vehiculo.tiene_cajuela:
                continue
        
        # 3. Calcular la distancia hacia el cliente
        distancia = calcular_distancia(
            chofer.latitud, chofer.longitud,
            viaje.origen_lat, viaje.origen_lng
        )
        
        candidatos_validos.append({
            'chofer': chofer,
            'distancia': distancia
        })

    if not candidatos_validos:
        return None

    # Ordenar por el chofer más cercano
    candidatos_validos.sort(key=lambda x: x['distancia'])
    return candidatos_validos[0]['chofer']


class SolicitarViajeSerializer(serializers.Serializer):
    origen_lat = serializers.FloatField()
    origen_lng = serializers.FloatField()
    origen_direccion = serializers.CharField(required=False, allow_blank=True, default="")
    destino_lat = serializers.FloatField()
    destino_lng = serializers.FloatField()
    destino_direccion = serializers.CharField(required=False, allow_blank=True, default="")
    asientos = serializers.IntegerField(default=1, min_value=1)
    requiere_cajuela = serializers.BooleanField(default=False)


class SolicitarViajeView(APIView):
    """Antes: api_solicitar_viaje_especial. El cliente sale de request.user."""
    permission_classes = [IsAuthenticated, EsCliente]

    def post(self, request):
        serializer = SolicitarViajeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        datos = serializer.validated_data

        viaje = Viaje.objects.create(
            cliente=request.user,
            origen_lat=datos["origen_lat"],
            origen_lng=datos["origen_lng"],
            origen_direccion=datos["origen_direccion"],
            destino_lat=datos["destino_lat"],
            destino_lng=datos["destino_lng"],
            destino_direccion=datos["destino_direccion"],
            asientos_solicitados=datos["asientos"],
            requiere_cajuela=datos["requiere_cajuela"],
            estado="solicitado",
        )

        return Response(
            {
                "status": "ok",
                "viaje_id": viaje.id,
                "message": "Solicitud creada. Buscando chofer disponible.",
            },
            status=status.HTTP_201_CREATED,
        )


class SolicitarColectivoView(APIView):
    """Asignación automática obligatoria de colectivos (sin aprobación manual)."""
    permission_classes = [IsAuthenticated, EsCliente]

    def post(self, request):
        serializer = SolicitarViajeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        datos = serializer.validated_data

        # En colectivos se asigna de inmediato por obligación de ruta
        viaje = Viaje.objects.create(
            cliente=request.user,
            origen_lat=datos["origen_lat"],
            origen_lng=datos["origen_lng"],
            origen_direccion=datos["origen_direccion"],
            destino_lat=datos["destino_lat"],
            destino_lng=datos["destino_lng"],
            destino_direccion=datos["destino_direccion"],
            asientos_solicitados=datos["asientos"],
            requiere_cajuela=datos["requiere_cajuela"],
            estado="aceptado",
        )

        # Asignar automáticamente evaluando asientos, cajuela y proximidad
        chofer_asignado = asignar_colectivo_automatico(viaje)

        if not chofer_asignado:
            viaje.estado = "solicitado"
            viaje.save()
            return Response(
                {"status": "error", "message": "No hay colectivos disponibles con los requisitos solicitados en este momento."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Vincular chofer al viaje y descontar asientos temporalmente
        viaje.chofer = chofer_asignado
        viaje.save()

        chofer_asignado.asientos_disponibles -= datos["asientos"]
        chofer_asignado.save(update_fields=["asientos_disponibles"])

        # Notificar en tiempo real al grupo personal del chofer mediante WebSockets
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"chofer_{chofer_asignado.id}",
            {
                "type": "notificar_cliente_colectivo",
                "viaje_id": viaje.id,
                "cliente_nombre": f"{request.user.nombre or ''} {request.user.apellido or ''}".strip(),
                "lat": datos["origen_lat"],
                "lng": datos["origen_lng"],
                "asientos": datos["asientos"],
                "requiere_cajuela": datos["requiere_cajuela"],
            }
        )

        return Response(
            {
                "status": "ok",
                "viaje_id": viaje.id,
                "message": "Colectivo asignado correctamente.",
                "chofer": {
                    "id": chofer_asignado.id,
                    "nombre": f"{chofer_asignado.perfil.nombre} {chofer_asignado.perfil.apellido}",
                    "vehiculo": f"{chofer_asignado.vehiculo.marca} {chofer_asignado.vehiculo.modelo} ({chofer_asignado.vehiculo.placas})" if chofer_asignado.vehiculo else "Unidad activa"
                }
            },
            status=status.HTTP_201_CREATED,
        )


class CalificacionSerializer(serializers.Serializer):
    viaje_id = serializers.IntegerField()
    puntaje = serializers.IntegerField(min_value=1, max_value=5)
    comentario = serializers.CharField(required=False, allow_blank=True, default="")


class CalificarViajeView(APIView):
    """Antes: api_crear_calificacion, ahora con validacion de dueño y estado."""
    permission_classes = [IsAuthenticated, EsCliente]

    def post(self, request):
        serializer = CalificacionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        datos = serializer.validated_data

        try:
            viaje = Viaje.objects.get(id=datos["viaje_id"])
        except Viaje.DoesNotExist:
            return Response(
                {"status": "error", "message": "Viaje no encontrado."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if viaje.cliente_id != request.user.id_usuario:
            return Response(
                {"status": "error", "message": "Este viaje no pertenece a tu cuenta."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if viaje.estado != "terminado":
            return Response(
                {"status": "error", "message": "Solo puedes calificar viajes terminados."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if hasattr(viaje, "calificacion"):
            return Response(
                {"status": "error", "message": "Este viaje ya fue calificado."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        calificacion = Calificacion.objects.create(
            viaje=viaje,
            puntaje=datos["puntaje"],
            comentario=datos["comentario"],
        )

        return Response(
            {
                "status": "ok",
                "calificacion_id": calificacion.id,
                "message": "Calificacion guardada exitosamente.",
            },
            status=status.HTTP_201_CREATED,
        )


class MisViajesView(APIView):
    """
    Nuevo (no existia antes): lista los viajes del cliente autenticado.
    Sin esto la app no tiene forma de mostrar el historial del cliente.
    """
    permission_classes = [IsAuthenticated, EsCliente]

    def get(self, request):
        viajes = Viaje.objects.filter(cliente=request.user).order_by("-fecha_creacion")[:50]
        data = [
            {
                "id": v.id,
                "estado": v.estado,
                "origen_direccion": v.origen_direccion,
                "destino_direccion": v.destino_direccion,
                "fecha_creacion": v.fecha_creacion,
                "calificado": hasattr(v, "calificacion"),
            }
            for v in viajes
        ]
        return Response({"viajes": data}, status=status.HTTP_200_OK)