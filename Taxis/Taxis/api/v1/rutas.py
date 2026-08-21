"""
Ubicacion: Taxis/Taxis/api/v1/rutas.py

Los choferes circulan libremente y atienden cualquier ruta.
"""
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
    """Formula de Haversine."""
    R = 6371
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def _ruta_a_dict(ruta):
    # Como los choferes andan libres, devolvemos una lista general de choferes activos 
    # o dejamos la lista vacía/general para el panel si no hay asignación fija.
    choferes_qs = Chofer.objects.filter(estado__in=["activo", "en_ruta"])

    choferes_data = []
    for chofer in choferes_qs:
        choferes_data.append({
            "id": chofer.id,
            "nombre": getattr(getattr(chofer, 'perfil', None), 'nombre', str(chofer)),
            "estado_display": getattr(chofer, 'estado', 'Inactivo')
        })

    return {
        "id": ruta.id,
        "nombre": ruta.nombre,
        "descripcion": getattr(ruta, 'descripcion', ''),
        "trazado": ruta.trazado or [],
        "choferes_asignados": choferes_data,
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


class SolicitarColectivoSerializer(serializers.Serializer):
    ruta_id = serializers.IntegerField()
    lat = serializers.FloatField()
    lng = serializers.FloatField()
    asientos = serializers.IntegerField(default=1, min_value=1)
    requiere_cajuela = serializers.BooleanField(default=False)


class SolicitarColectivoView(APIView):
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

        # Buscamos entre todos los choferes activos y con cupo, sin importar una ruta fija
        candidatos = Chofer.objects.filter(
            estado__in=["activo", "en_ruta"],
            asientos_disponibles__gte=datos["asientos"],
        ).select_related("perfil", "vehiculo")

        if datos["requiere_cajuela"]:
            candidatos = candidatos.filter(vehiculo__tiene_cajuela=True)

        candidatos = list(candidatos)
        if not candidatos:
            return Response(
                {"status": "error", "message": "No hay colectivos con cupo disponible en el sistema ahora mismo."},
                status=status.HTTP_404_NOT_FOUND,
            )

        candidatos.sort(
            key=lambda c: _distancia_km(datos["lat"], datos["lng"], c.latitud or 0.0, c.longitud or 0.0)
        )

        chofer_elegido = None
        for candidato in candidatos:
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
                origen_direccion="Parada de colectivo",
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
    authentication_classes = [PerfilUsuarioJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        rutas = Ruta.objects.all().order_by("nombre")
        data = []
        for ruta in rutas:
            # Contamos todos los choferes activos generales disponibles en el sistema
            disponibles = Chofer.objects.filter(
                estado__in=["activo", "en_ruta"],
                asientos_disponibles__gt=0
            ).count()
            data.append({
                "id": ruta.id,
                "nombre": ruta.nombre,
                "descripcion": ruta.descripcion or "",
                "trazado": ruta.trazado or [],
                "choferes_disponibles": disponibles,
            })
        return Response({"rutas": data}, status=status.HTTP_200_OK)