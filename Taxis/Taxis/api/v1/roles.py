"""
Ubicacion: Taxis/Taxis/api/v1/roles.py

Gestion de roles/turnos por grupo, para el panel React.
Reemplaza api_roles (views.py). El pago del rol (lado chofer) ya vive en
api/v1/choferes.py (PagarRolView) -- este archivo es solo la administracion
de las reglas, no el pago.

Con un solo admin global (confirmado), no se filtra por Base todavia.
"""
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ...models import Chofer, RolDia
from ...permissions import EsAdmin

DIAS_OPCIONES = ["Lunes", "Martes", "Miercoles", "Jueves", "Viernes", "Sabado", "Domingo"]


class RolesConfigView(APIView):
    """GET: configuracion actual de grupos/dias + choferes disponibles para asignar."""
    permission_classes = [IsAuthenticated, EsAdmin]

    def get(self, request):
        grupos_configurados = {}
        for r in RolDia.objects.all():
            grupos_configurados.setdefault(r.grupo, []).append(r.dia_semana)

        choferes = Chofer.objects.select_related("perfil").exclude(estado="pendiente")
        choferes_data = [
            {
                "id": c.id,
                "perfil": {
                    "nombre": c.perfil.nombre or "",
                    "apellido": c.perfil.apellido or "",
                    "telefono": getattr(c.perfil, "telefono", ""),
                },
                "estado": c.estado,
                "estado_display": c.get_estado_display(),
                "grupo_rol": c.grupo_rol or "",
            }
            for c in choferes
        ]

        return Response(
            {
                "grupos_configurados": grupos_configurados,
                "choferes": choferes_data,
                "dias_opciones": DIAS_OPCIONES,
            },
            status=status.HTTP_200_OK,
        )


class GuardarReglaSerializer(serializers.Serializer):
    grupo = serializers.CharField()
    dias = serializers.ListField(child=serializers.CharField(), allow_empty=False)

    def validate_dias(self, value):
        invalidos = [d for d in value if d not in DIAS_OPCIONES]
        if invalidos:
            raise serializers.ValidationError(f"Dias invalidos: {invalidos}")
        return value


class GuardarReglaRolView(APIView):
    """POST: crea/reemplaza los dias asignados a un grupo."""
    permission_classes = [IsAuthenticated, EsAdmin]

    def post(self, request):
        serializer = GuardarReglaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        datos = serializer.validated_data

        RolDia.objects.filter(grupo=datos["grupo"]).delete()
        for dia in datos["dias"]:
            RolDia.objects.create(grupo=datos["grupo"], dia_semana=dia)

        return Response(
            {"status": "ok", "message": f"Dias asignados al {datos['grupo']}."},
            status=status.HTTP_200_OK,
        )


class EliminarGrupoSerializer(serializers.Serializer):
    grupo = serializers.CharField()


class EliminarGrupoRolView(APIView):
    """POST: elimina un grupo de rol y desasigna a los choferes que lo tenian."""
    permission_classes = [IsAuthenticated, EsAdmin]

    def post(self, request):
        serializer = EliminarGrupoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        grupo = serializer.validated_data["grupo"]

        RolDia.objects.filter(grupo=grupo).delete()
        Chofer.objects.filter(grupo_rol=grupo).update(grupo_rol=None)

        return Response(
            {"status": "ok", "message": f"Se elimino el {grupo}."},
            status=status.HTTP_200_OK,
        )


class AsignarChoferGrupoSerializer(serializers.Serializer):
    chofer_id = serializers.IntegerField()
    grupo_rol = serializers.CharField(required=False, allow_blank=True, default="")


class AsignarChoferGrupoView(APIView):
    """POST: asigna (o quita, si grupo_rol viene vacio) un chofer a un grupo."""
    permission_classes = [IsAuthenticated, EsAdmin]

    def post(self, request):
        serializer = AsignarChoferGrupoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        datos = serializer.validated_data

        try:
            chofer = Chofer.objects.get(id=datos["chofer_id"])
        except Chofer.DoesNotExist:
            return Response(
                {"status": "error", "message": "Chofer no encontrado."},
                status=status.HTTP_404_NOT_FOUND,
            )

        chofer.grupo_rol = datos["grupo_rol"] or None
        chofer.save()

        return Response(
            {"status": "ok", "message": "Chofer actualizado correctamente."},
            status=status.HTTP_200_OK,
        )