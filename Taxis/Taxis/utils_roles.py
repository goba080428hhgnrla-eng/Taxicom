import datetime
from django.db import transaction

DIAS_OPCIONES = ["Lunes", "Martes", "Miercoles", "Jueves", "Viernes", "Sabado", "Domingo"]

def rebalancear_todos_los_choferes():
    """
    Toma a TODOS los choferes aprobados y los reparte de manera 
    completamente equitativa entre los grupos creados, 
    ordenados estrictamente por fecha de registro.
    """
    from .models import Chofer, RolDia

    grupos_existentes = list(RolDia.objects.values_list('grupo', flat=True).distinct().order_by('grupo'))
    if not grupos_existentes:
        return

    choferes = Chofer.objects.exclude(estado='pendiente').order_by('perfil__fecha_registro')
    num_grupos = len(grupos_existentes)

    with transaction.atomic():
        for i, chofer in enumerate(choferes):
            grupo_destino = grupos_existentes[i % num_grupos]
            if chofer.grupo_rol != grupo_destino:
                Chofer.objects.filter(pk=chofer.pk).update(grupo_rol=grupo_destino)


def asignar_grupo_automatico_a_chofer(chofer):
    """
    Asigna un grupo individual al chofer entrante buscando 
    cuál grupo tiene MENOS integrantes actualmente.
    """
    from .models import Chofer, RolDia

    grupos_existentes = list(RolDia.objects.values_list('grupo', flat=True).distinct().order_by('grupo'))
    if not grupos_existentes:
        return

    # Contar cuántos choferes tiene cada grupo actualmente
    conteo_grupos = {}
    for g in grupos_existentes:
        conteo_grupos[g] = Chofer.objects.filter(grupo_rol=g).count()

    # Seleccionar el grupo con menor cantidad de choferes
    grupo_menos_poblado = min(conteo_grupos, key=conteo_grupos.get)
    
    Chofer.objects.filter(pk=chofer.pk).update(grupo_rol=grupo_menos_poblado)


def obtener_dias_semana_grupo(grupo_nombre, fecha_ref=None):
    """
    Calcula qué días le corresponden al grupo en la semana actual mediante rotación.
    """
    from .models import RolDia

    if not fecha_ref:
        fecha_ref = datetime.date.today()

    grupos = list(RolDia.objects.values_list('grupo', flat=True).distinct().order_by('grupo'))
    if not grupos or grupo_nombre not in grupos:
        return []

    num_semana = fecha_ref.isocalendar()[1]
    num_grupos = len(grupos)
    idx_grupo = grupos.index(grupo_nombre)

    # Rotación por número de semana
    posicion_rotada = (idx_grupo + num_semana) % num_grupos
    grupo_rotado = grupos[posicion_rotada]

    return list(RolDia.objects.filter(grupo=grupo_rotado).values_list('dia_semana', flat=True))