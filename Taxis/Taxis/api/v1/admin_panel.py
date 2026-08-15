"""
Ubicacion: Taxis/Taxis/api/v1/admin_panel.py

Endpoints para el panel React de administracion.
Reemplazan api_gestion_choferes y lista_usuarios (views.py).

Todos requieren EsAdmin. Nota: hoy NO filtran por Base (un admin ve todos
los choferes de todas las bases) -- eso queda pendiente hasta que se decida
migrar el AdministradorBase/multi-tenancy completo. Si tienes un solo admin
global por ahora, no es urgente; si ya tienes admins por base, avisame y
cambiamos EsAdmin por EsAdminDeSuBase + un filtro por base en los querysets.
"""
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ...models import Chofer, PerfilUsuario
from ...permissions import EsAdmin
from django.db import transaction


def _serializar_chofer(c: Chofer) -> dict:
    return {
        "id": c.id,
        "perfil": {
            "nombre": c.perfil.nombre or "",
            "apellido": c.perfil.apellido or "",
            "telefono": getattr(c.perfil, "telefono", ""),
        },
        "vehiculo": (
            {
                "marca": c.vehiculo.marca,
                "modelo": c.vehiculo.modelo,
                "anio": getattr(c.vehiculo, "anio", ""),
                "placas": c.vehiculo.placas,
            }
            if c.vehiculo
            else {}
        ),
        "estado": c.estado,
        "estado_display": c.get_estado_display(),
    }


class ListaChoferesView(APIView):
    """GET: pendientes + activos. Antes: parte GET de api_gestion_choferes."""
    permission_classes = [IsAuthenticated, EsAdmin]

    def get(self, request):
        pendientes = Chofer.objects.filter(estado="pendiente").select_related(
            "perfil", "vehiculo"
        )
        activos = Chofer.objects.filter(
            estado__in=["activo", "en_ruta"]
        ).select_related("perfil", "vehiculo")

        return Response(
            {
                "pendientes": [_serializar_chofer(c) for c in pendientes],
                "activos": [_serializar_chofer(c) for c in activos],
            },
            status=status.HTTP_200_OK,
        )


class GestionChoferSerializer(serializers.Serializer):
    chofer_id = serializers.IntegerField()
    accion = serializers.ChoiceField(choices=["aceptar", "rechazar"])
    motivo = serializers.CharField(required=False, allow_blank=True, default="")


class GestionChoferView(APIView):
    """
    POST: aceptar o rechazar un chofer pendiente.
    Antes: parte POST de api_gestion_choferes (y gestion_choferes en views.py).

    - aceptar  -> estado='activo'
    - rechazar -> estado='inactivo'  (el chofer se entera por notificacion /
      o consultando su propio estado la proxima vez que la app llame al
      endpoint de perfil; si quieres feedback inmediato, esto es un buen
      lugar para disparar un Notificacion + push FCM en el futuro)
    """
    permission_classes = [IsAuthenticated, EsAdmin]

    def post(self, request):
        serializer = GestionChoferSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        datos = serializer.validated_data

        try:
            chofer = Chofer.objects.select_related("perfil").get(id=datos["chofer_id"])
        except Chofer.DoesNotExist:
            return Response(
                {"status": "error", "message": "Chofer no encontrado."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if chofer.estado != "pendiente":
            return Response(
                {
                    "status": "error",
                    "message": f"Este chofer ya fue procesado (estado actual: {chofer.estado}).",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if datos["accion"] == "aceptar":
            chofer.estado = "activo"
            mensaje = "Chofer aceptado y activado."
        else:  # rechazar
            chofer.estado = "inactivo"
            mensaje = "Chofer rechazado."
            # Aqui es donde, cuando exista el modelo Notificacion en uso,
            # registrarias el motivo del rechazo para que el chofer lo vea
            # en la app:
            #   Notificacion.objects.create(
            #       usuario=chofer.perfil,
            #       tipo="asignacion_viaje",  # o un tipo nuevo "rechazo_chofer"
            #       mensaje=datos["motivo"] or "Tu solicitud fue rechazada.",
            #   )

        chofer.save()

        return Response(
            {"status": "ok", "message": mensaje, "chofer_id": chofer.id, "nuevo_estado": chofer.estado},
            status=status.HTTP_200_OK,
        )


class ListaUsuariosView(APIView):
    """Antes: lista_usuarios (views.py)."""
    permission_classes = [IsAuthenticated, EsAdmin]

    def get(self, request):
        usuarios = PerfilUsuario.objects.all().order_by("-fecha_registro")
        data = [
            {
                "id_usuario": u.id_usuario,
                "nombre": f"{u.nombre or ''} {u.apellido or ''}".strip(),
                "correo": u.email,
                "telefono": u.telefono,
                "rol": u.rol,
                "fecha_registro": u.fecha_registro,
            }
            for u in usuarios
        ]
        return Response({"usuarios": data}, status=status.HTTP_200_OK)


class MapaChoferesActivosView(APIView):
    """
    Antes: api_choferes_activos_mapa (views.py). Mapa en tiempo real para
    el panel React -- choferes activos/en_ruta con su ubicacion.
    """
    permission_classes = [IsAuthenticated, EsAdmin]

    def get(self, request):
        choferes = Chofer.objects.filter(
            estado__in=["activo", "en_ruta"]
        ).select_related("perfil", "vehiculo")

        data = []
        for c in choferes:
            if c.latitud and c.longitud and float(c.latitud) != 0.0:
                data.append(
                    {
                        "chofer_id": c.id,
                        "nombre": f"{c.perfil.nombre or ''} {c.perfil.apellido or ''}".strip(),
                        "vehiculo": f"{c.vehiculo.marca} {c.vehiculo.modelo}" if c.vehiculo else "Vehiculo",
                        "sketchfab_id": c.vehiculo.sketchfab_model_id if c.vehiculo else "",
                        "asientos_disponibles": c.asientos_disponibles,
                        "lat": float(c.latitud),
                        "lng": float(c.longitud),
                        "estado": c.get_estado_display(),
                    }
                )

        return Response({"choferes": data}, status=status.HTTP_200_OK)
    
    
class DetalleChoferView(APIView):
    """
    GET: Devuelve el expediente completo del chofer y su vehículo.
    DELETE: Elimina el chofer del sistema en caso de incidencia.
    """
    permission_classes = [IsAuthenticated, EsAdmin]

    def get(self, request, chofer_id):
        try:
            chofer = Chofer.objects.select_related("perfil", "vehiculo").get(id=chofer_id)
        except Chofer.DoesNotExist:
            return Response(
                {"status": "error", "message": "Chofer no encontrado."},
                status=status.HTTP_404_NOT_FOUND,
            )

        v = chofer.vehiculo
        p = chofer.perfil

        data = {
            "id": chofer.id,
            "estado": chofer.estado,
            "estado_display": chofer.get_estado_display(),
            "grupo_rol": getattr(chofer, "grupo_rol", "Sin asignar"),
            "asientos_disponibles": chofer.asientos_disponibles,
            "perfil": {
                "id_usuario": p.id_usuario,
                "nombre": p.nombre or "",
                "apellido": p.apellido or "",
                "email": p.email,
                "telefono": getattr(p, "telefono", ""),
                "rol": p.rol,
                "fecha_registro": p.fecha_registro.strftime("%Y-%m-%d %H:%M") if p.fecha_registro else None,
            },
            "vehiculo": {
                "id": v.id,
                "marca": v.marca,
                "modelo": v.modelo,
                "anio": getattr(v, "anio", ""),
                "placas": v.placas,
                "color": getattr(v, "color", "No especificado"),
            } if v else None
        }
        return Response(data, status=status.HTTP_200_OK)

    def delete(self, request, chofer_id):
        try:
            chofer = Chofer.objects.select_related("perfil").get(id=chofer_id)
        except Chofer.DoesNotExist:
            return Response(
                {"status": "error", "message": "Chofer no encontrado."},
                status=status.HTTP_404_NOT_FOUND,
            )

        motivo = request.data.get("motivo", "Falta administrativa / Incidencia")

        with transaction.atomic():
            nombre = f"{chofer.perfil.nombre} {chofer.perfil.apellido}".strip()
            # Elimina la entidad chofer
            chofer.delete()

        return Response(
            {"status": "ok", "message": f"Chofer {nombre} dado de baja exitosamente."},
            status=status.HTTP_200_OK,
        )    