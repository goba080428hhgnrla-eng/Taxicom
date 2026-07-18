from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.hashers import check_password
from django.shortcuts import get_object_or_404
from .models import PerfilUsuario, Chofer, Viaje, Vehiculo
import json

@csrf_exempt
def api_login(request):
    """
    Endpoint de inicio de sesión compatible con la app Android (Volley).
    Soporta autenticación por nombre de usuario o correo electrónico.
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)
        
    try:
        data = json.loads(request.body)
        correo_o_user = data.get('correo') or data.get('username')
        password = data.get('password')
        
        if not correo_o_user or not password:
            return JsonResponse({'status': 'error', 'message': 'Faltan credenciales'}, status=400)
            
        # Búsqueda flexible en PerfilUsuario
        try:
            if '@' in correo_o_user:
                usuario = PerfilUsuario.objects.get(email=correo_o_user)
            else:
                usuario = PerfilUsuario.objects.get(username=correo_o_user)
        except PerfilUsuario.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'El usuario no existe'}, status=404)
            
        # Validar contraseña utilizando el hashing nativo de Django
        if usuario.check_password(password):
            respuesta = {
                'status': 'ok',
                'id': usuario.id_usuario,
                'nombre': f"{usuario.nombre} {usuario.apellido or ''}".strip(),
                'correo': usuario.email,
                'rol': usuario.rol,
                'es_chofer': usuario.es_chofer,
                'es_admin': usuario.es_admin
            }
            return JsonResponse(respuesta)
        else:
            return JsonResponse({'status': 'error', 'message': 'Contraseña incorrecta'}, status=401)
            
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@csrf_exempt
def api_cambiar_modalidad_chofer(request):
    """
    Permite al chofer cambiar su estado operativo en tiempo real:
    - 'activo': Disponible para Colectivo / Libre.
    - 'en_ruta': Asignado a una ruta fija o viaje especial en curso.
    - 'inactivo': Desconectado.
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)
        
    try:
        data = json.loads(request.body)
        usuario_id = data.get('usuario_id')
        nuevo_estado = data.get('estado') # 'activo', 'en_ruta', 'inactivo'
        
        chofer = get_object_or_404(Chofer, perfil__id_usuario=usuario_id)
        if nuevo_estado in dict(Chofer.ESTADOS):
            chofer.estado = nuevo_estado
            chofer.save()
            return JsonResponse({'status': 'ok', 'message': f'Estado cambiado a {chofer.get_estado_display()}'})
        return JsonResponse({'status': 'error', 'message': 'Estado inválido'}, status=400)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@csrf_exempt
def api_solicitar_viaje_especial(request):
    """
    Crea una solicitud de viaje exclusivo (Estilo Uber clásico).
    Registra el origen, destino y los asientos requeridos por el cliente.
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)
        
    try:
        data = json.loads(request.body)
        cliente_id = data.get('cliente_id')
        
        cliente = get_object_or_404(PerfilUsuario, id_usuario=cliente_id)
        
        viaje = Viaje.objects.create(
            cliente=cliente,
            origen_lat=float(data['origen_lat']),
            origen_lng=float(data['origen_lng']),
            origen_direccion=data.get('origen_direccion', ''),
            destino_lat=float(data['destino_lat']),
            destino_lng=float(data['destino_lng']),
            destino_direccion=data.get('destino_direccion', ''),
            asientos_solicitados=int(data.get('asientos', 1)),
            requiere_cajuela=bool(data.get('requiere_cajuela', False)),
            estado='solicitado'
        )
        
        # Opcional: Aquí puedes implementar lógica para notificar por Firebase Cloud Messaging (FCM) 
        # a los choferes cercanos que estén 'activos' utilizando su campo fcm_token.
        
        return JsonResponse({
            'status': 'ok',
            'viaje_id': viaje.id,
            'message': 'Buscando chofer disponible para viaje especial.'
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    
@csrf_exempt
def api_registro_cliente(request):
    """
    Endpoint para registrar un nuevo cliente desde la aplicación móvil.
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)
        
    try:
        data = json.loads(request.body)
        nombre = data.get('nombre')
        apellido = data.get('apellido', '')
        email = data.get('correo') or data.get('email')
        password = data.get('password')
        telefono = data.get('telefono', '')
        
        if not nombre or not email or not password:
            return JsonResponse({'status': 'error', 'message': 'Faltan campos obligatorios'}, status=400)
            
        if PerfilUsuario.objects.filter(email=email).exists():
            return JsonResponse({'status': 'error', 'message': 'El correo ya está registrado'}, status=400)
            
        # Creamos un username basado en el email
        username = email.split('@')[0]
        if PerfilUsuario.objects.filter(username=username).exists():
            username = f"{username}_{PerfilUsuario.objects.count()}"

        usuario = PerfilUsuario.objects.create(
            username=username,
            nombre=nombre,
            apellido=apellido,
            email=email,
            password_hash=password, # El método save() lo encriptará automáticamente
            telefono=telefono,
            es_cliente=True,
            es_chofer=False,
            es_admin=False
        )
        
        return JsonResponse({
            'status': 'ok',
            'message': 'Usuario registrado correctamente',
            'id_usuario': usuario.id_usuario
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)    