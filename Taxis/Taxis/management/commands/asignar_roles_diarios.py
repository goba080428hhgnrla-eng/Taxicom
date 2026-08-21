from django.core.management.base import BaseCommand
from django.utils import timezone
from Taxis.models import Chofer, RolDia, Base, PagoRol

class Command(BaseCommand):
    help = 'Asigna los roles diarios a los choferes, gestiona pagos y aplica el arrastre de turnos no cubiertos.'

    def handle(self, *args, **options):
        hoy = timezone.now().date()
        
        # Mapeo de dias
        dias_semana = ['Lunes', 'Martes', 'Miercoles', 'Jueves', 'Viernes', 'Sabado', 'Domingo']
        dia_hoy = dias_semana[hoy.weekday()]
        
        # Buscar los grupos que trabajan hoy según la rotación
        roles_hoy = RolDia.objects.filter(dia_semana=dia_hoy).values_list('grupo', flat=True)
        if not roles_hoy:
            self.stdout.write("Hoy no hay grupos programados.")
            return

        base_por_defecto = Base.objects.first()
        if not base_por_defecto:
            self.stdout.write("Error: No hay una Base registrada para asignar.")
            return

        choferes_grupo = Chofer.objects.filter(grupo_rol__in=roles_hoy)
        contador_activos = 0
        contador_inactivos = 0
        contador_arrastre = 0

        for chofer in choferes_grupo:
            # 1. Verificar si pagó el día de hoy
            pago_hoy = PagoRol.objects.filter(chofer=chofer, fecha_pago__date=hoy, estado='pagado').exists()
            
            # 2. Verificar si tiene pagos pendientes o turnos anteriores sin resolver (ARRASTRE)
            tiene_deuda_anterior = PagoRol.objects.filter(
                chofer=chofer, 
                fecha_pago__date__lt=hoy, 
                estado__in=['pendiente', 'rechazado']
            ).exists()

            if pago_hoy and not tiene_deuda_anterior:
                # Si pagó hoy y está al día con lo anterior, se activa
                chofer.base = base_por_defecto
                chofer.estado = 'activo'
                chofer.save()
                contador_activos += 1
            else:
                # Si no pagó hoy O tiene adeudos acumulados del pasado, se aplica el arrastre (inactivo/moroso)
                chofer.base = None
                chofer.estado = 'inactivo'
                chofer.save()
                
                if tiene_deuda_anterior:
                    contador_arrastre += 1
                else:
                    contador_inactivos += 1

        self.stdout.write(
            f"Proceso completado: {contador_activos} activos, "
            f"{contador_inactivos} inactivos de hoy, "
            f"{contador_arrastre} con turnos/pagos arrastrados pendientes."
        )