from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone

from ...models import Chofer, RolDia, PagoRol
from ...permissions import EsAdmin
from ...utils import enviar_notificacion
from ...utils_roles import obtener_dias_semana_grupo

class RolesConfigView(APIView):
    """GET: Devuelve el estado actual de los grupos, los choferes y los pagos pendientes."""
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

        # Lista de choferes asignados automáticamente
        choferes = Chofer.objects.select_related("perfil").exclude(estado="pendiente").order_by('perfil__fecha_registro')
        choferes_data = [
            {
                "id": c.id,
                "nombre": f"{c.perfil.nombre or ''} {c.perfil.apellido or ''}".strip() or c.perfil.username,
                "telefono": getattr(c.perfil, "telefono", ""),
                "estado": c.get_estado_display(),
                "grupo_rol": c.grupo_rol or "Auto-asignando...",
                "al_dia": PagoRol.objects.filter(chofer=c, fecha_pago__date=hoy, estado='pagado').exists(),
            }
            for c in choferes
        ]

        # COBROS EN EFECTIVO PENDIENTES DE REVISAR POR EL ADMIN
        pagos_pendientes = PagoRol.objects.filter(estado='pendiente').select_related('chofer__perfil')
        pagos_pendientes_data = [
            {
                "id": p.id,
                "chofer_nombre": f"{p.chofer.perfil.nombre or ''} {p.chofer.perfil.apellido or ''}".strip(),
                "monto": p.monto,
                "fecha": p.fecha_pago.strftime("%Y-%m-%d %H:%M"),
            }
            for p in pagos_pendientes
        ]

        return Response({
            "grupos_configurados": grupos_configurados,
            "choferes": choferes_data,
            "pagos_pendientes": pagos_pendientes_data,
        }, status=status.HTTP_200_OK)


class ConfirmarPagoEfectivoView(APIView):
    """POST: ÚNICA ACCIÓN MANUAL DEL ADMIN - Confirmar que recibió el dinero en efectivo."""
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
                mensaje=f"Tu pago de rol por ${pago.monto} en efectivo fue confirmado por administración."
            )
            return Response({"status": "ok", "message": "Pago en efectivo confirmado correctamente."})
        else:
            pago.estado = 'rechazado'
            pago.save()
            return Response({"status": "ok", "message": "Pago marcado como rechazado."})