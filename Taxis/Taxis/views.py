from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.db.models import Q
from .models import Chofer, RolDia, PerfilUsuario, RolDia

# Importamos tu nuevo decorador independiente
from .decorators import login_panel_required

def home_publico(request):
    """1.- Home público con información del sitio de taxis"""
    return render(request, 'taxis/home.html')


def login_personalizado(request):
    if request.method == 'POST':
        usuario_input = request.POST.get('username') # Lo que ponga el usuario en el input
        password_input = request.POST.get('password')

        try:
            usuario = PerfilUsuario.objects.get(
                Q(username=usuario_input) | Q(email=usuario_input)
            )
            
            # Validamos la contraseña usando tu método personalizado
            if usuario.check_password(password_input):
                if usuario.es_admin: 
                    request.session['usuario_id'] = usuario.id_usuario
                    request.session['usuario_rol'] = usuario.rol 
                    request.session['usuario_nombre'] = usuario.nombre
                    return redirect('admin_dashboard')
                else:
                    messages.error(request, "Acceso denegado. No eres administrador.")
            else:
                messages.error(request, "Contraseña incorrecta.")
                
        except PerfilUsuario.DoesNotExist:
            messages.error(request, "El usuario o correo no existe en el sistema.")

    return render(request, 'taxis/login.html')


def logout_personalizado(request):
    """Elimina las variables de sesión manuales"""
    if 'usuario_id' in request.session:
        del request.session['usuario_id']
    if 'usuario_rol' in request.session:
        del request.session['usuario_rol']
    if 'usuario_nombre' in request.session:
        del request.session['usuario_nombre']
    
    request.session.flush() # Destruye la sesión por completo
    return redirect('home_publico')

@login_panel_required
def admin_dashboard(request):
    choferes_activos = Chofer.objects.filter(estado__in=['activo', 'en_ruta'])
    context = {
        'choferes': choferes_activos,
    }
    return render(request, 'taxis/dashboard.html', context)

def gestion_choferes(request):
    if request.method == "POST":
        chofer_id = request.POST.get("chofer_id")
        accion = request.POST.get("accion")
        
        try:
            chofer = Chofer.objects.get(id=chofer_id)
            if accion == "aceptar":
                chofer.estado = "activo"  
            elif accion == "rechazar":
                chofer.estado = "inactivo"
            chofer.save()
        except Chofer.DoesNotExist:
            pass
            
        return redirect('gestion_choferes')

    pendientes = Chofer.objects.filter(estado='pendiente').select_related('perfil', 'vehiculo')
    
    activos = Chofer.objects.filter(estado__in=['activo', 'en_ruta']).select_related('perfil', 'vehiculo')

    context = {
        'pendientes': pendientes,
        'activos': activos,
    }
    return render(request, 'gestion_choferes.html', context)

@login_panel_required
def asignar_roles(request):
    """Asignar grupos y días de rol de cada grupo"""
    if request.method == 'POST':
        grupo = request.POST.get('grupo')
        dias_seleccionados = request.POST.getlist('dias')
        
        RolDia.objects.filter(grupo=grupo).delete()
        for dia in dias_seleccionados:
            RolDia.objects.create(grupo=grupo, dia_semana=dia)
            
        return redirect('asignar_roles')
        
    roles = RolDia.objects.all()
    dias_opciones = ['Lunes', 'Martes', 'Miercoles', 'Jueves', 'Viernes', 'Sabado', 'Domingo']
    return render(request, 'taxis/roles.html', {
        'roles': roles,
        'dias_opciones': dias_opciones
    })
    
    
@login_panel_required
def lista_usuarios(request):
    """Muestra la lista de todos los usuarios registrados en nuestra base de datos propia"""
    # Trae a todos los usuarios ordenados por fecha de registro
    usuarios_registrados = PerfilUsuario.objects.all().order_by('-fecha_registro')
    
    return render(request, 'taxis/lista_usuarios.html', {
        'usuarios': usuarios_registrados
    })    
    
    
@login_panel_required
def asignar_roles(request):
    """
    Controla de manera flexible la asignación de días de servicio a los diferentes grupos
    y permite vincular manualmente a los choferes a dichos grupos.
    """
    if request.method == 'POST':
        accion = request.POST.get('accion')
        
        # ACCIÓN 1: GUARDAR O ACTUALIZAR DÍAS DE UN GRUPO
        if accion == 'guardar_regla':
            grupo = request.POST.get('grupo', '').strip()
            dias_seleccionados = request.POST.getlist('dias')
            
            if not grupo:
                messages.error(request, "Debes especificar el nombre del grupo.")
                return redirect('asignar_roles')
                
            if not dias_seleccionados:
                messages.error(request, f"Debes seleccionar al menos un día para el {grupo}.")
                return redirect('asignar_roles')

            RolDia.objects.filter(grupo=grupo).delete()
            for dia in dias_seleccionados:
                RolDia.objects.create(grupo=grupo, dia_semana=dia)
                
            messages.success(request, f"Días de rol asignados correctamente al {grupo}.")
            
        # ACCIÓN 2: ELIMINAR UN GRUPO Y SUS REGLAS
        elif accion == 'eliminar_grupo':
            grupo = request.POST.get('grupo', '').strip()
            if grupo:
                RolDia.objects.filter(grupo=grupo).delete()
                # Quitamos a los choferes de ese grupo ya que dejó de existir
                Chofer.objects.filter(grupo_rol=grupo).update(grupo_rol=None)
                messages.success(request, f"Se eliminaron todas las reglas del {grupo}.")

        # ACCIÓN 3: ASIGNAR UN CHOFER A UN GRUPO DE MANERA MANUAL
        elif accion == 'asignar_chofer':
            chofer_id = request.POST.get('chofer_id')
            grupo_destino = request.POST.get('grupo_rol', '').strip()
            
            chofer = get_object_or_404(Chofer, id=chofer_id)
            
            if grupo_destino == "":
                chofer.grupo_rol = None  # Se remueve del grupo (Fuera de Rol)
                messages.success(request, f"Se ha removido a {chofer.perfil.nombre} de su grupo.")
            else:
                chofer.grupo_rol = grupo_destino
                messages.success(request, f"Chofer {chofer.perfil.nombre} asignado con éxito al {grupo_destino}.")
                
            chofer.save()
                
        return redirect('asignar_roles')
        
    # --- PROCESAMIENTO GET (RENDERIZAR VISTA) ---
    roles_queryset = RolDia.objects.all()
    
    # Agrupar los días por cada grupo para la tabla superior
    grupos_configurados = {}
    for r in roles_queryset:
        if r.grupo not in grupos_configurados:
            grupos_configurados[r.grupo] = []
        grupos_configurados[r.grupo].append(r.dia_semana)
        
    # Obtener choferes aprobados/activos para listarlos
    choferes = Chofer.objects.select_related('perfil').exclude(estado='pendiente')
    
    # Lista limpia de nombres de grupos disponibles para el menú desplegable (Select)
    lista_grupos = list(grupos_configurados.keys())
    
    dias_opciones = ['Lunes', 'Martes', 'Miercoles', 'Jueves', 'Viernes', 'Sabado', 'Domingo']
    
    context = {
        'grupos_configurados': grupos_configurados,
        'choferes': choferes,
        'lista_grupos': lista_grupos,
        'dias_opciones': dias_opciones,
    }
    
    return render(request, 'taxis/roles.html', context)

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.gis.geos import Point  # Si usas GeoDjango, de lo contrario guarda lat/lng normales
import json


@csrf_exempt
def actualizar_ubicacion_chofer(request):
    """
    Endpoint invocado por la App de Android.
    Valida si el chofer está aprobado (activo) antes de actualizar su ubicación.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            perfil_id = data.get('perfil_id')
            latitud = data.get('latitud')
            longitud = data.get('longitud')

            chofer = Chofer.objects.get(perfil__id_usuario=perfil_id)

            # Restricción: Si el admin no lo ha aprobado, no entra
            if chofer.estado == 'pendiente':
                return JsonResponse({
                    'error': 'Tu solicitud aún no ha sido aprobada por el administrador.'
                }, status=403)

            if chofer.estado == 'inactivo':
                return JsonResponse({
                    'error': 'Tu cuenta de chofer se encuentra desactivada.'
                }, status=403)

            # Actualizamos la posición
            chofer.latitud = latitud
            chofer.longitud = longitud
            # O si usas campo Point: chofer.ubicacion = Point(float(longitud), float(latitud))
            chofer.save()

            return JsonResponse({'status': 'ok', 'message': 'Ubicación actualizada'}, status=200)

        except Chofer.DoesNotExist:
            return JsonResponse({'error': 'Perfil de chofer no encontrado.'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Método no permitido'}, status=405)


@login_panel_required
def api_choferes_activos_mapa(request):
    """
    Devuelve los choferes activos/en ruta con sus coordenadas actualizadas para el dashboard del admin.
    """
    choferes = Chofer.objects.filter(estado__in=['activo', 'en_ruta']).select_related('perfil', 'vehiculo')
    data = []
    
    for c in choferes:
        if c.latitud and c.longitud:
            data.append({
                'id': c.id,
                'nombre': c.perfil.nombre,
                'placas': c.vehiculo.placas if c.vehiculo else 'S/N',
                'vehiculo': f"{c.vehiculo.marca} {c.vehiculo.modelo}" if c.vehiculo else 'Vehículo',
                'lat': float(c.latitud),
                'lng': float(c.longitud),
                'estado': c.estado,
            })

    return JsonResponse({'choferes': data}, status=200)