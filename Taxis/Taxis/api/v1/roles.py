from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone

from ...models import Chofer, RolDia, PagoRol
from ...permissions import EsAdmin
from ...utils import enviar_notificacion
from ...utils_roles import rebalancear_todos_los_choferes, obtener_dias_semana_grupo, DIAS_OPCIONES


class RolesConfigView(APIView):
    """GET: Retorna el estado de los grupos, los choferes asignados automáticamente y cobros pendientes."""
    permission_classes = [IsAuthenticated, EsAdmin]

    def get(self, request):
        hoy = timezone.now().date()
        grupos_nombres = RolDia.objects.values_list('grupo', flat=True).distinct().order_by('grupo')
        
        grupos_configurados = []
        for g in grupos_nombres:
            dias_esta_semana = obtener_dias_semana_grupo(g, fecha_ref=hoy)
            total_choferes = Chofer.objects.filter(grupo_rol=g).count()
            grupos_configurados.append({
                "nombre": g,
                "dias_semana_actual": dias_esta_semana,
                "total_choferes": total_choferes,
            })

        # Choferes y su asignación automática
        choferes = Chofer.objects.select_related("perfil").exclude(estado="pendiente").order_by('perfil__fecha_registro')
        choferes_data = []
        for c in choferes:
            al_dia = PagoRol.objects.filter(chofer=c, fecha_pago__date=hoy, estado='pagado').exists()
            
            choferes_data.append({
                "id": c.id,
                "nombre": f"{c.perfil.nombre or ''} {c.perfil.apellido or ''}".strip() or c.perfil.username,
                "telefono": getattr(c.perfil, "telefono", ""),
                "estado": c.estado,
                "estado_display": c.get_estado_display(),
                "grupo_rol": c.grupo_rol or "Asignando...",
                "al_dia": al_dia,
            })

        # Cobros en efectivo reportados o pendientes de liberar
        pagos_pendientes = PagoRol.objects.filter(estado='pendiente').select_related('chofer__perfil')
        pagos_pendientes_data = [
            {
                "id": p.id,
                "chofer_id": p.chofer.id,
                "chofer_nombre": f"{p.chofer.perfil.nombre or ''} {p.chofer.perfil.apellido or ''}".strip(),
                "monto": p.monto,
                "fecha": p.fecha_pago.strftime("%Y-%m-%d %H:%M"),
            }
            for p in pagos_pendientes
        ]

        return Response(
            {
                "grupos_configurados": grupos_configurados,
                "choferes": choferes_data,
                "pagos_pendientes": pagos_pendientes_data,
                "dias_opciones": DIAS_OPCIONES,
            },
            status=status.HTTP_200_OK,
        )


class GuardarReglaSerializer(serializers.Serializer):
    grupo = serializers.CharField()
    dias = serializers.ListField(child=serializers.CharField(), allow_empty=False)


class GuardarReglaRolView(APIView):
    """POST: Crea un grupo y automáticamente distribuye de manera equitativa a los choferes."""
    permission_classes = [IsAuthenticated, EsAdmin]

    def post(self, request):
        serializer = GuardarReglaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        datos = serializer.validated_data

        RolDia.objects.filter(grupo=datos["grupo"]).delete()
        for dia in datos["dias"]:
            RolDia.objects.create(grupo=datos["grupo"], dia_semana=dia)

        # AL CREAR/MODIFICAR UN GRUPO SE REBALANCEAN AUTOMÁTICAMENTE
        rebalancear_todos_los_choferes()

        return Response(
            {"status": "ok", "message": f"Grupo '{datos['grupo']}' guardado. Choferes reasignados automáticamente."},
            status=status.HTTP_200_OK,
        )


class EliminarGrupoRolView(APIView):
    """POST: Elimina un grupo y rebalancea los choferes entre los grupos restantes."""
    permission_classes = [IsAuthenticated, EsAdmin]

    def post(self, request):
        grupo = request.data.get("grupo")
        if not grupo:
            return Response({"status": "error", "message": "Grupo no especificado."}, status=400)

        RolDia.objects.filter(grupo=grupo).delete()
        Chofer.objects.filter(grupo_rol=grupo).update(grupo_rol=None)

        # REBALANCEO AUTOMÁTICO EN GRUPOS RESTANTES
        rebalancear_todos_los_choferes()

        return Response(
            {"status": "ok", "message": f"Se eliminó el grupo '{grupo}' y se reasignaron los choferes."},
            status=status.HTTP_200_OK,
        )


class ConfirmarPagoEfectivoView(APIView):
    """POST: El admin presiona 'Confirmar Cobro' cuando recibe el dinero en efectivo."""
    permission_classes = [IsAuthenticated, EsAdmin]

    def post(self, request):
        pago_id = request.data.get("pago_id")
        aprobado = request.data.get("aprobado", True)

        try:
            pago = PagoRol.objects.get(id=pago_id)
        except PagoRol.DoesNotExist:
            return Response({"status": "error", "message": "Pago no encontrado."}, status=404)

        if aprobado:
            pago.estado = 'pagado'
            pago.liberado_por = request.user
            pago.save()

            chofer = pago.chofer
            if chofer.estado == 'inactivo':
                chofer.estado = 'activo'
                chofer.save(update_fields=['estado'])

            enviar_notificacion(
                usuario=chofer.perfil,
                tipo='pago_rol',
                mensaje=f"Tu pago de rol por ${pago.monto} ha sido recibido en efectivo y confirmado."
            )
            return Response({"status": "ok", "message": "Pago en efectivo confirmado. Chofer liberado."})
        else:
            pago.estado = 'rechazado'
            pago.save()
            return Response({"status": "ok", "message": "Cobro/Pago marcado como rechazado."})