import math

from django.db import transaction
from django.db.models import F
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from rest_framework import serializers, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from Taxis.models import Ruta, Chofer, Viaje
from Taxis.permissions import EsAdmin, EsCliente
from Taxis.authentication import PerfilUsuarioJWTAuthentication


def _distancia_km(lat1, lng1, lat2, lng2):
    """Formula de Haversine -- suficiente precision para elegir 'el mas cercano'."""
    R = 6371
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def _ruta_a_dict(ruta: Ruta) -> dict:
    choferes = ruta.choferes.select_related("perfil", "vehiculo").all()
    return {
        "id": ruta.id,
        "nombre": ruta.nombre,
        "descripcion": ruta.descripcion or "",
        "trazado": ruta.trazado or [],
        "choferes_asignados": [
            {
                "id": c.id,
                "nombre": f"{c.perfil.nombre or ''} {c.perfil.apellido or ''}".strip(),
                "estado": c.estado,
                "estado_display": c.get_estado_display(),
                "asientos_disponibles": c.asientos_disponibles,
                "tiene_cajuela": c.vehiculo.tiene_cajuela if c.vehiculo else False,
            }
            for c in choferes
        ],
    }


class RutaSerializer(serializers.Serializer):
    nombre = serializers.CharField()
    descripcion = serializers.CharField(required=False, allow_blank=True, default="")
    trazado = serializers.ListField(child=serializers.ListField(child=serializers.FloatField()), required=False, default=list)


class RutasListCreateView(APIView):
    authentication_classes = [PerfilUsuarioJWTAuthentication]
    permission_classes = [IsAuthenticated, EsAdmin]

    def get(self, request):
        rutas = Ruta.objects.all().order_by("nombre")
        return Response({"rutas": [_ruta_a_dict(r) for r in rutas]}, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = RutaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ruta = Ruta.objects.create(**serializer.validated_data)
        return Response(_ruta_a_dict(ruta), status=status.HTTP_201_CREATED)


class RutaDetailView(APIView):
    authentication_classes = [PerfilUsuarioJWTAuthentication]
    permission_classes = [IsAuthenticated, EsAdmin]

    def patch(self, request, ruta_id):
        try:
            ruta = Ruta.objects.get(id=ruta_id)
        except Ruta.DoesNotExist:
            return Response({"status": "error", "message": "Ruta no encontrada."}, status=status.HTTP_404_NOT_FOUND)

        serializer = RutaSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        for campo, valor in serializer.validated_data.items():
            setattr(ruta, campo, valor)
        ruta.save()
        return Response(_ruta_a_dict(ruta), status=status.HTTP_200_OK)

    def delete(self, request, ruta_id):
        try:
            ruta = Ruta.objects.get(id=ruta_id)
        except Ruta.DoesNotExist:
            return Response({"status": "error", "message": "Ruta no encontrada."}, status=status.HTTP_404_NOT_FOUND)
        ruta.delete()
        return Response({"status": "ok"}, status=status.HTTP_200_OK)


class ChoferIdSerializer(serializers.Serializer):
    chofer_id = serializers.IntegerField()


class AgregarChoferRutaView(APIView):
    """POST {"chofer_id": N} -- suma este chofer a la ruta (no quita a nadie mas)."""
    authentication_classes = [PerfilUsuarioJWTAuthentication]
    permission_classes = [IsAuthenticated, EsAdmin]

    def post(self, request, ruta_id):
        try:
            ruta = Ruta.objects.get(id=ruta_id)
        except Ruta.DoesNotExist:
            return Response({"status": "error", "message": "Ruta no encontrada."}, status=status.HTTP_404_NOT_FOUND)

        serializer = ChoferIdSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            chofer = Chofer.objects.get(id=serializer.validated_data["chofer_id"])
        except Chofer.DoesNotExist:
            return Response({"status": "error", "message": "Chofer no encontrado."}, status=status.HTTP_404_NOT_FOUND)

        chofer.ruta_asignada = ruta
        chofer.save()
        return Response(_ruta_a_dict(ruta), status=status.HTTP_200_OK)


class QuitarChoferRutaView(APIView):
    """POST {"chofer_id": N} -- saca a este chofer de la ruta, sin tocar a los demas."""
    authentication_classes = [PerfilUsuarioJWTAuthentication]
    permission_classes = [IsAuthenticated, EsAdmin]

    def post(self, request, ruta_id):
        try:
            ruta = Ruta.objects.get(id=ruta_id)
        except Ruta.DoesNotExist:
            return Response({"status": "error", "message": "Ruta no encontrada."}, status=status.HTTP_404_NOT_FOUND)

        serializer = ChoferIdSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        Chofer.objects.filter(id=serializer.validated_data["chofer_id"], ruta_asignada=ruta).update(ruta_asignada=None)
        return Response(_ruta_a_dict(ruta), status=status.HTTP_200_OK)


class SolicitarColectivoSerializer(serializers.Serializer):
    ruta_id = serializers.IntegerField()
    lat = serializers.FloatField()
    lng = serializers.FloatField()
    asientos = serializers.IntegerField(default=1, min_value=1)
    requiere_cajuela = serializers.BooleanField(default=False)


class SolicitarColectivoView(APIView):
    """
    Elige, entre TODOS los choferes activos en la ruta con asientos y
    cajuela suficientes, al mas cercano al cliente. Le reserva los
    asientos de forma atomica (evita que dos solicitudes casi simultaneas
    le ganen el mismo asiento al mismo chofer) y le manda la alerta SOLO
    a el.
    """
    authentication_classes = [PerfilUsuarioJWTAuthentication]
    permission_classes = [IsAuthenticated, EsCliente]

    def post(self, request):
        serializer = SolicitarColectivoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        datos = serializer.validated_data

        try:
            ruta = Ruta.objects.get(id=datos["ruta_id"])
        except Ruta.DoesNotExist:
            return Response({"status": "error", "message": "Ruta no encontrada."}, status=status.HTTP_404_NOT_FOUND)

        candidatos = Chofer.objects.filter(
            ruta_asignada=ruta,
            estado__in=["activo", "en_ruta"],
            asientos_disponibles__gte=datos["asientos"],
        ).select_related("perfil", "vehiculo")

        if datos["requiere_cajuela"]:
            candidatos = candidatos.filter(vehiculo__tiene_cajuela=True)

        candidatos = list(candidatos)
        if not candidatos:
            return Response(
                {"status": "error", "message": "No hay colectivos con cupo disponible en esa ruta ahora mismo."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Ordena por cercania real al cliente -- el mas cercano va primero.
        candidatos.sort(
            key=lambda c: _distancia_km(datos["lat"], datos["lng"], c.latitud or 0.0, c.longitud or 0.0)
        )

        chofer_elegido = None
        for candidato in candidatos:
            # UPDATE atomico: solo resta los asientos si TODAVIA hay
            # suficientes en este instante.
            filas_actualizadas = Chofer.objects.filter(
                id=candidato.id, asientos_disponibles__gte=datos["asientos"]
            ).update(asientos_disponibles=F("asientos_disponibles") - datos["asientos"])

            if filas_actualizadas:
                chofer_elegido = candidato
                break

        if chofer_elegido is None:
            return Response(
                {"status": "error", "message": "Los colectivos cercanos se llenaron justo ahora, intenta de nuevo."},
                status=status.HTTP_409_CONFLICT,
            )

        with transaction.atomic():
            viaje = Viaje.objects.create(
                cliente=request.user,
                chofer=chofer_elegido,
                origen_lat=datos["lat"],
                origen_lng=datos["lng"],
                origen_direccion="Parada de colectivo (ubicación exacta del cliente)",
                destino_lat=datos["lat"],
                destino_lng=datos["lng"],
                destino_direccion="",
                asientos_solicitados=datos["asientos"],
                requiere_cajuela=datos["requiere_cajuela"],
                estado="solicitado",
            )

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"chofer_{chofer_elegido.id}",
            {
                "type": "notificar_cliente_colectivo",
                "viaje_id": viaje.id,
                "cliente_nombre": f"{request.user.nombre or ''} {request.user.apellido or ''}".strip(),
                "lat": datos["lat"],
                "lng": datos["lng"],
                "asientos": datos["asientos"],
                "requiere_cajuela": datos["requiere_cajuela"],
            },
        )

        return Response(
            {
                "status": "ok",
                "viaje_id": viaje.id,
                "message": f"Solicitud enviada a {chofer_elegido.perfil.nombre or 'tu colectivo'}.",
            },
            status=status.HTTP_201_CREATED,
        )


class RutasClienteView(APIView):
    """
    GET: lista de rutas colectivas para que el cliente elija -- sin datos
    de administracion, solo lo necesario para dibujar el mapa y saber si
    hay cupo.
    """
    authentication_classes = [PerfilUsuarioJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        rutas = Ruta.objects.all().order_by("nombre")
        data = []
        for ruta in rutas:
            disponibles = ruta.choferes.filter(
                estado__in=["activo", "en_ruta"], asientos_disponibles__gt=0
            ).count()
            data.append({
                "id": ruta.id,
                "nombre": ruta.nombre,
                "descripcion": ruta.descripcion or "",
                "trazado": ruta.trazado or [],
                "choferes_disponibles": disponibles,
            })
        return Response({"rutas": data}, status=status.HTTP_200_OK)


# =====================================================================
# VISTAS NUEVAS: INTERVENCIÓN MANUAL DEL CHOFER
# =====================================================================

class MisPasajerosActivosView(APIView):
    """
    GET: Devuelve la lista de solicitudes/pasajeros activos asignados
    al chofer autenticado, junto con su conteo actual de asientos.
    """
    authentication_classes = [PerfilUsuarioJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        usuario = request.user
        if not hasattr(usuario, "chofer_datos"):
            return Response({"status": "error", "message": "El usuario no es chofer."}, status=status.HTTP_403_FORBIDDEN)

        chofer = usuario.chofer_datos
        viajes = Viaje.objects.filter(chofer=chofer, estado__in=["solicitado", "aceptado", "en_curso"]).order_by("-fecha_creacion")
        
        data = [
            {
                "viaje_id": v.id,
                "cliente_nombre": f"{v.cliente.nombre or ''} {v.cliente.apellido or ''}".strip(),
                "asientos": v.asientos_solicitados,
                "requiere_cajuela": v.requiere_cajuela,
                "lat": v.origen_lat,
                "lng": v.origen_lng,
                "estado": v.estado,
                "hora": v.fecha_creacion.strftime("%H:%M"),
            }
            for v in viajes
        ]
        return Response(
            {
                "asientos_disponibles": chofer.asientos_disponibles,
                "total_capacidad": chofer.vehiculo.total_asientos if chofer.vehiculo else 4,
                "pasajeros": data,
            },
            status=status.HTTP_200_OK,
        )


class MarcarSubidaPasajeroView(APIView):
    """
    POST /api/v1/choferes/colectivo/subio/<viaje_id>/
    El chofer presiona un botón para confirmar que el cliente ya subió.
    Cambia el estado del viaje a 'en_curso'.
    """
    authentication_classes = [PerfilUsuarioJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, viaje_id):
        try:
            viaje = Viaje.objects.get(id=viaje_id)
        except Viaje.DoesNotExist:
            return Response({"status": "error", "message": "Viaje no encontrado."}, status=status.HTTP_404_NOT_FOUND)

        viaje.estado = "en_curso"
        viaje.save()
        return Response({"status": "ok", "message": "Pasajero abordado."}, status=status.HTTP_200_OK)


class MarcarBajadaPasajeroView(APIView):
    """
    POST /api/v1/choferes/colectivo/bajo/<viaje_id>/
    El chofer indica manualmente que el cliente bajó.
    Cambia el estado a 'terminado' y libera exactamente la cantidad
    de asientos que ese pasajero/grupo ocupaba.
    """
    authentication_classes = [PerfilUsuarioJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, viaje_id):
        try:
            viaje = Viaje.objects.get(id=viaje_id)
        except Viaje.DoesNotExist:
            return Response({"status": "error", "message": "Viaje no encontrado."}, status=status.HTTP_404_NOT_FOUND)

        if viaje.estado in ["terminado", "cancelado"]:
            return Response({"status": "error", "message": "Este pasajero ya había descendido."}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            viaje.estado = "terminado"
            viaje.save()
            
            chofer = viaje.chofer
            if chofer:
                capacidad_maxima = chofer.vehiculo.total_asientos if chofer.vehiculo else 4
                
                # Devolución de asientos
                Chofer.objects.filter(id=chofer.id).update(
                    asientos_disponibles=F("asientos_disponibles") + viaje.asientos_solicitados
                )
                
                # Tope de seguridad para no sobrepasar el total del vehículo
                chofer.refresh_from_db()
                if chofer.asientos_disponibles > capacidad_maxima:
                    chofer.asientos_disponibles = capacidad_maxima
                    chofer.save()

        return Response(
            {
                "status": "ok",
                "message": "Pasajero bajó del colectivo.",
                "asientos_disponibles": chofer.asientos_disponibles if chofer else 0,
            },
            status=status.HTTP_200_OK,
        )


class ResetearColectivoView(APIView):
    """
    POST /api/v1/choferes/colectivo/reset-asientos/
    Restablece manualmente la capacidad máxima del vehículo al instante.
    Útil si el colectivo se vacía en terminal/base.
    """
    authentication_classes = [PerfilUsuarioJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        usuario = request.user
        if not hasattr(usuario, "chofer_datos"):
            return Response({"status": "error", "message": "El usuario no es chofer."}, status=status.HTTP_403_FORBIDDEN)

        chofer = usuario.chofer_datos
        max_asientos = chofer.vehiculo.total_asientos if chofer.vehiculo else 4
        
        chofer.asientos_disponibles = max_asientos
        chofer.save()

        # Cierra todas las solicitudes que estuvieran abiertas
        Viaje.objects.filter(chofer=chofer, estado__in=["solicitado", "aceptado", "en_curso"]).update(estado="terminado")

        return Response(
            {
                "status": "ok",
                "message": f"Colectivo reiniciado a {max_asientos} asientos libres.",
                "asientos_disponibles": chofer.asientos_disponibles,
            },
            status=status.HTTP_200_OK,
        )