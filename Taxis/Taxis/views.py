import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .models import Chofer, RolDia, PerfilUsuario
from .decorators import login_panel_required


def home_publico(request):
    return render(request, 'taxis/home.html')


def login_personalizado(request):
    if request.method == 'POST':
        usuario_input = request.POST.get('username')
        password_input = request.POST.get('password')

        try:
            usuario = PerfilUsuario.objects.get(
                Q(username=usuario_input) | Q(email=usuario_input)
            )
            
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
    request.session.flush()
    return redirect('home_publico')


@login_panel_required
def admin_dashboard(request):
    """
    Optimizado con select_related para evitar el problema de la consulta N+1.
    """
    choferes_activos = Chofer.objects.filter(
        estado__in=['activo', 'en_ruta']
    ).select_related('perfil', 'vehiculo')
    
    context = {
        'choferes': choferes_activos,
    }
    return render(request, 'taxis/dashboard.html', context)


@login_panel_required
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
    return render(request, 'taxis/gestion_choferes.html', context)


@login_panel_required
def lista_usuarios(request):
    usuarios_registrados = PerfilUsuario.objects.all().order_by('-fecha_registro')
    return render(request, 'taxis/lista_usuarios.html', {'usuarios': usuarios_registrados})


@login_panel_required
def asignar_roles(request):
    if request.method == 'POST':
        accion = request.POST.get('accion')
        
        if accion == 'guardar_regla':
            grupo = request.POST.get('grupo', '').strip()
            dias_seleccionados = request.POST.getlist('dias')
            
            if not grupo or not dias_seleccionados:
                messages.error(request, "Debes especificar grupo y seleccionar días.")
                return redirect('asignar_roles')

            RolDia.objects.filter(grupo=grupo).delete()
            for dia in dias_seleccionados:
                RolDia.objects.create(grupo=grupo, dia_semana=dia)
                
            messages.success(request, f"Días asignados al {grupo}.")
            
        elif accion == 'eliminar_grupo':
            grupo = request.POST.get('grupo', '').strip()
            if grupo:
                RolDia.objects.filter(grupo=grupo).delete()
                Chofer.objects.filter(grupo_rol=grupo).update(grupo_rol=None)
                messages.success(request, f"Se eliminó el {grupo}.")

        elif accion == 'asignar_chofer':
            chofer_id = request.POST.get('chofer_id')
            grupo_destino = request.POST.get('grupo_rol', '').strip()
            chofer = get_object_or_404(Chofer, id=chofer_id)
            
            chofer.grupo_rol = grupo_destino if grupo_destino else None
            chofer.save()
            messages.success(request, f"Chofer actualizado correctamente.")
                
        return redirect('asignar_roles')

    roles_queryset = RolDia.objects.all()
    grupos_configurados = {}
    for r in roles_queryset:
        if r.grupo not in grupos_configurados:
            grupos_configurados[r.grupo] = []
        grupos_configurados[r.grupo].append(r.dia_semana)
        
    choferes = Chofer.objects.select_related('perfil').exclude(estado='pendiente')
    lista_grupos = list(grupos_configurados.keys())
    dias_opciones = ['Lunes', 'Martes', 'Miercoles', 'Jueves', 'Viernes', 'Sabado', 'Domingo']
    
    return render(request, 'taxis/roles.html', {
        'grupos_configurados': grupos_configurados,
        'choferes': choferes,
        'lista_grupos': lista_grupos,
        'dias_opciones': dias_opciones,
    })


@csrf_exempt
def actualizar_ubicacion_chofer(request):
    """Endpoint API para la App de Android (Sin GDAL)"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            perfil_id = data.get('perfil_id')
            latitud = data.get('latitud')
            longitud = data.get('longitud')

            chofer = Chofer.objects.get(perfil__id_usuario=perfil_id)

            if chofer.estado in ['pendiente', 'inactivo']:
                return JsonResponse({'error': 'Chofer no autorizado o inactivo.'}, status=403)

            chofer.latitud = float(latitud)
            chofer.longitud = float(longitud)
            chofer.save()

            return JsonResponse({'status': 'ok', 'message': 'Ubicación actualizada'}, status=200)

        except Chofer.DoesNotExist:
            return JsonResponse({'error': 'Perfil de chofer no encontrado.'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Método no permitido'}, status=405)


@login_panel_required
def api_choferes_activos_mapa(request):
    """API JSON para consultar posiciones en tiempo real"""
    choferes = Chofer.objects.filter(estado__in=['activo', 'en_ruta']).select_related('perfil', 'vehiculo')
    data = []
    
    for c in choferes:
        if c.latitud and c.longitud and float(c.latitud) != 0.0:
            data.append({
                'chofer_id': c.id,
                'nombre': f"{c.perfil.nombre or ''} {c.perfil.apellido or ''}".strip(),
                'vehiculo': f"{c.vehiculo.marca} {c.vehiculo.modelo}" if c.vehiculo else 'Vehículo',
                'sketchfab_id': c.vehiculo.sketchfab_model_id if c.vehiculo else '',
                'asientos_disponibles': c.asientos_disponibles,
                'lat': float(c.latitud),
                'lng': float(c.longitud),
                'estado': c.get_estado_display(),
            })

    return JsonResponse({'choferes': data}, status=200)


#Apis de react 

import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from .models import Chofer, RolDia, PerfilUsuario

# ==========================================
# ENDPOINTS API REST PARA EL PANEL WEB REACT
# ==========================================

@csrf_exempt
def api_web_login(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)
    try:
        data = json.loads(request.body)
        usuario_input = data.get('username')
        password_input = data.get('password')

        usuario = PerfilUsuario.objects.get(
            Q(username=usuario_input) | Q(email=usuario_input)
        )
        if usuario.check_password(password_input):
            if usuario.es_admin:
                request.session['usuario_id'] = usuario.id_usuario
                request.session['usuario_nombre'] = usuario.nombre
                return JsonResponse({
                    'status': 'ok',
                    'usuario': {'id': usuario.id_usuario, 'nombre': usuario.nombre, 'email': usuario.email}
                })
            return JsonResponse({'status': 'error', 'message': 'Acceso denegado. No eres administrador.'}, status=403)
        return JsonResponse({'status': 'error', 'message': 'Contraseña incorrecta.'}, status=401)
    except PerfilUsuario.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Usuario o correo no encontrado.'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


def api_gestion_choferes(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            chofer_id = data.get("chofer_id")
            accion = data.get("accion")
            
            chofer = Chofer.objects.get(id=chofer_id)
            if accion == "aceptar":
                chofer.estado = "activo"
            elif accion == "rechazar":
                chofer.estado = "inactivo"
            chofer.save()
            return JsonResponse({'status': 'ok'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    pendientes = Chofer.objects.filter(estado='pendiente').select_related('perfil', 'vehiculo')
    activos = Chofer.objects.filter(estado__in=['activo', 'en_ruta']).select_related('perfil', 'vehiculo')

    def serialize(query):
        return [{
            'id': c.id,
            'perfil': {'nombre': c.perfil.nombre or '', 'apellido': c.perfil.apellido or '', 'telefono': getattr(c.perfil, 'telefono', '')},
            'vehiculo': {'marca': c.vehiculo.marca, 'modelo': c.vehiculo.modelo, 'anio': getattr(c.vehiculo, 'anio', ''), 'placas': c.vehiculo.placas} if c.vehiculo else {},
            'estado': c.estado,
            'estado_display': c.get_estado_display()
        } for c in query]

    return JsonResponse({'pendientes': serialize(pendientes), 'activos': serialize(activos)})


def api_roles(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            accion = data.get('accion')

            if accion == 'guardar_regla':
                grupo = data.get('grupo', '').strip()
                dias = data.get('dias', [])
                RolDia.objects.filter(grupo=grupo).delete()
                for d in dias:
                    RolDia.objects.create(grupo=grupo, dia_semana=d)

            elif accion == 'eliminar_grupo':
                grupo = data.get('grupo', '').strip()
                RolDia.objects.filter(grupo=grupo).delete()
                Chofer.objects.filter(grupo_rol=grupo).update(grupo_rol=None)

            elif accion == 'asignar_chofer':
                chofer_id = data.get('chofer_id')
                grupo_destino = data.get('grupo_rol', '').strip()
                chofer = Chofer.objects.get(id=chofer_id)
                chofer.grupo_rol = grupo_destino if grupo_destino else None
                chofer.save()

            return JsonResponse({'status': 'ok'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    roles_queryset = RolDia.objects.all()
    grupos_configurados = {}
    for r in roles_queryset:
        if r.grupo not in grupos_configurados:
            grupos_configurados[r.grupo] = []
        grupos_configurados[r.grupo].append(r.dia_semana)

    choferes = Chofer.objects.select_related('perfil').exclude(estado='pendiente')
    choferes_data = [{
        'id': c.id,
        'perfil': {'nombre': c.perfil.nombre or '', 'apellido': c.perfil.apellido or '', 'telefono': getattr(c.perfil, 'telefono', '')},
        'estado': c.estado,
        'estado_display': c.get_estado_display(),
        'grupo_rol': c.grupo_rol or ''
    } for c in choferes]

    return JsonResponse({
        'grupos_configurados': grupos_configurados,
        'choferes': choferes_data,
        'dias_opciones': ['Lunes', 'Martes', 'Miercoles', 'Jueves', 'Viernes', 'Sabado', 'Domingo']
    })