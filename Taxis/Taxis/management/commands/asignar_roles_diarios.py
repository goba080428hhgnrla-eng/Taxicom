from django.core.management.base import BaseCommand
from Taxis.models import Chofer, RolDia, Base

class Command(BaseCommand):
    help = 'Asigna los roles diarios a los choferes según su grupo'

    def handle(self, *args, **options):
        from django.utils import timezone
        hoy = timezone.now().date()
        
        #mapeo de dias en español a numeros 0=Lunes, 6=Domingo
        dias_semana = ['Lunes', 'Martes', 'Miercoles', 'Jueves', 'Viernes', 'Sabado', 'Domingo']
        dia_hoy = dias_semana[hoy.weekday()]
        
        # buscar grupos los grupos que trabajan hoy
        roles_hoy = RolDia.objects.filter(dia_semana=dia_hoy).values_list('grupo', flat=True)

        if not roles_hoy:
            self.stdout.write("Hoy no hay grupos programados.")
            return

        #asignar Base a los choferes de ese grupo
        #supongamos que queremos asignarlos a la primera base disponible
        base_por_defecto = Base.objects.first()
        
        if not base_por_defecto:
            self.stdout.write("Error: No hay una Base registrada para asignar.")
            return

        choferes_actualizados = Chofer.objects.filter(grupo_rol__in=roles_hoy).update(base=base_por_defecto)

        self.stdout.write(f"Se asignó la base a {choferes_actualizados} choferes del grupo {roles_hoy}.")