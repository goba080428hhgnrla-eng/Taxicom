import datetime
from django.db import transaction
from datetime import date, timedelta
from Taxis.models import PagoRol, Chofer

DIAS_SEMANA = ["Lunes", "Martes", "Miercoles", "Jueves", "Viernes", "Sabado", "Domingo"]

def garantizar_grupos_y_asignar_chofer(chofer):
    """
    1. Asegura que existan 3 grupos base (Grupo A, Grupo B, Grupo C).
    2. Asegura que los 7 días de la semana estén repartidos entre los grupos para cobertura total.
    3. Asigna al chofer al grupo que tenga MENOS integrantes en ese momento.
    """
    from .models import Chofer, RolDia

    grupos_base = ["Grupo A", "Grupo B", "Grupo C"]

    with transaction.atomic():
        # Crear reglas de días si no existen aún en la base de datos
        if not RolDia.objects.exists():
            for i, dia in enumerate(DIAS_SEMANA):
                grupo_destino = grupos_base[i % len(grupos_base)]
                RolDia.objects.create(grupo=grupo_destino, dia_semana=dia)

        # Si el chofer ya tiene grupo y no es necesario moverlo, terminamos
        if chofer.grupo_rol:
            return

        # Contar cuántos choferes hay en cada grupo
        conteo = {g: Chofer.objects.filter(grupo_rol=g).count() for g in grupos_base}
        grupo_menos_poblado = min(conteo, key=conteo.get)

        # Asignar automáticamente
        Chofer.objects.filter(pk=chofer.pk).update(grupo_rol=grupo_menos_poblado)


def obtener_dias_semana_grupo(grupo_nombre, fecha_ref=None):
    """Calcula la rotación semanal inteligente según el número de semana del año."""
    from .models import RolDia

    if not fecha_ref:
        fecha_ref = datetime.date.today()

    grupos = list(RolDia.objects.values_list('grupo', flat=True).distinct().order_by('grupo'))
    if not grupos or grupo_nombre not in grupos:
        return []

    num_semana = fecha_ref.isocalendar()[1]
    num_grupos = len(grupos)
    idx_grupo = grupos.index(grupo_nombre)

    posicion_rotada = (idx_grupo + num_semana) % num_grupos
    grupo_rotado = grupos[posicion_rotada]

    return list(RolDia.objects.filter(grupo=grupo_rotado).values_list('dia_semana', flat=True))


def verificar_arrastre_turnos(chofer):
    """
    Verifica si el chofer tiene pagos o turnos pendientes de fechas pasadas 
    que no se hayan cubierto, aplicando el arrastre.
    """
    hoy = date.today()
    
    # Buscar si existen pagos pendientes o rechazados de días anteriores
    pagos_pendientes_atrasados = PagoRol.objects.filter(
        chofer=chofer,
        fecha_pago__date__lt=hoy,
        estado__in=['pendiente', 'rechazado']
    ).exists()

    if pagos_pendientes_atrasados:
        # El chofer mantiene el estatus de arrastre / adeudo
        if chofer.estado != 'inactivo':
            chofer.estado = 'inactivo'
            chofer.save(update_fields=['estado'])
        return False
        
    return True