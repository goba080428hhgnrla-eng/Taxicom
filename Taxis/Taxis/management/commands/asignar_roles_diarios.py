from django.core.management.base import BaseCommand
from Taxis.models import Chofer, RolDia, Base

class Command(BaseCommand):
    help = 'Asigna los roles diarios a los choferes según su grupo'

    def handle(self, *args, **options):
        from django.utils import timezone
        from Taxis.models import Chofer, RolDia, Base, PagoRol

        hoy = timezone.now().date()
        
        # Mapeo de dias
        dias_semana = ['Lunes', 'Martes', 'Miercoles', 'Jueves', 'Viernes', 'Sabado', 'Domingo']
        dia_hoy = dias_semana[hoy.weekday()]
        
        # Buscar los grupos que trabajan hoy
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

        for chofer in choferes_grupo:
            # verificar si pago hoy
            pago_hoy = PagoRol.objects.filter(chofer=chofer, fecha_pago__date=hoy, estado='pagado').exists()
            
            if pago_hoy:
                # Si pago se le asigna la base y se activa
                
                chofer.base = base_por_defecto
                chofer.estado = 'activo'
                chofer.save()
                contador_activos += 1
            else:
                # Si no pagó se le quita la base y se pone inactivo
                
                chofer.base = None
                chofer.estado = 'inactivo'
                chofer.save()
                contador_inactivos += 1

        self.stdout.write(f"Asignados: {contador_activos} activos, {contador_inactivos} inactivos (morosos).")