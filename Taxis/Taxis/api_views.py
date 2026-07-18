from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from .models import PerfilUsuario, Chofer, Viaje
import json


@csrf_exempt
def api_login(request):
    """
    Endpoint de inicio de sesión compatible con la app Android (Volley).
    Soporta autenticación por correo o nombre de usuario.
    """
    if request.method != 'POST':
        return JsonResponse({
            'status': 'error',
            'message': 'Método no permitido'
        }, status=405)

    try:
        data = json.loads(request.body)

        correo_o_user = data.get('correo') or data.get('username')
        password = data.get('password')

        if not correo_o_user or not password:
            return JsonResponse({
                'status': 'error',
                'message': 'Faltan credenciales'
            }, status=400)

        # Buscar por correo o username
        try:
            if '@' in correo_o_user:
                usuario = PerfilUsuario.objects.get(email=correo_o_user)
            else:
                usuario = PerfilUsuario.objects.get(username=correo_o_user)

        except PerfilUsuario.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'El usuario no existe'
            }, status=404)

        # Validar contraseña
        if not usuario.check_password(password):
            return JsonResponse({
                'status': 'error',
                'message': 'Contraseña incorrecta'
            }, status=401)

        # RESPUESTA PARA ANDROID
        return JsonResponse({
            "status": "ok",
            "id_usuario": usuario.id_usuario,
            "nombre": f"{usuario.nombre} {usuario.apellido or ''}".strip(),
            "correo": usuario.email,
            "rol": usuario.rol,
            "es_cliente": usuario.es_cliente,
            "es_chofer": usuario.es_chofer,
            "es_admin": usuario.es_admin
        })

    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error',
            'message': 'JSON inválido'
        }, status=400)

    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@csrf_exempt
def api_registro_cliente(request):
    """
    Registro de nuevos clientes desde Android.
    """
    if request.method != 'POST':
        return JsonResponse({
            'status': 'error',
            'message': 'Método no permitido'
        }, status=405)

    try:
        data = json.loads(request.body)

        nombre = data.get('nombre')
        apellido = data.get('apellido', '')
        email = data.get('correo') or data.get('email')
        password = data.get('password')
        telefono = data.get('telefono', '')

        if not nombre or not email or not password:
            return JsonResponse({
                'status': 'error',
                'message': 'Faltan campos obligatorios'
            }, status=400)

        if PerfilUsuario.objects.filter(email=email).exists():
            return JsonResponse({
                'status': 'error',
                'message': 'El correo ya está registrado'
            }, status=400)

        username = email.split('@')[0]

        contador = 1
        username_original = username

        while PerfilUsuario.objects.filter(username=username).exists():
            username = f"{username_original}{contador}"
            contador += 1

        usuario = PerfilUsuario.objects.create(
            username=username,
            nombre=nombre,
            apellido=apellido,
            email=email,
            password_hash=password,
            telefono=telefono,
            es_cliente=True,
            es_chofer=False,
            es_admin=False
        )

        return JsonResponse({
            "status": "ok",
            "message": "Usuario registrado correctamente",
            "id_usuario": usuario.id_usuario,
            "nombre": usuario.nombre,
            "correo": usuario.email
        })

    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error',
            'message': 'JSON inválido'
        }, status=400)

    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@csrf_exempt
def api_cambiar_modalidad_chofer(request):
    """
    Cambia el estado operativo del chofer.
    """
    if request.method != 'POST':
        return JsonResponse({
            'status': 'error',
            'message': 'Método no permitido'
        }, status=405)

    try:
        data = json.loads(request.body)

        usuario_id = data.get('usuario_id')
        nuevo_estado = data.get('estado')

        chofer = get_object_or_404(
            Chofer,
            perfil__id_usuario=usuario_id
        )

        if nuevo_estado not in dict(Chofer.ESTADOS):
            return JsonResponse({
                'status': 'error',
                'message': 'Estado inválido'
            }, status=400)

        chofer.estado = nuevo_estado
        chofer.save()

        return JsonResponse({
            'status': 'ok',
            'message': f'Estado cambiado a {chofer.get_estado_display()}'
        })

    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@csrf_exempt
def api_solicitar_viaje_especial(request):
    """
    Crear solicitud de viaje especial.
    """
    if request.method != 'POST':
        return JsonResponse({
            'status': 'error',
            'message': 'Método no permitido'
        }, status=405)

    try:
        data = json.loads(request.body)

        cliente = get_object_or_404(
            PerfilUsuario,
            id_usuario=data.get('cliente_id')
        )

        viaje = Viaje.objects.create(
            cliente=cliente,
            origen_lat=float(data["origen_lat"]),
            origen_lng=float(data["origen_lng"]),
            origen_direccion=data.get("origen_direccion", ""),
            destino_lat=float(data["destino_lat"]),
            destino_lng=float(data["destino_lng"]),
            destino_direccion=data.get("destino_direccion", ""),
            asientos_solicitados=int(data.get("asientos", 1)),
            requiere_cajuela=bool(data.get("requiere_cajuela", False)),
            estado="solicitado"
        )

        return JsonResponse({
            "status": "ok",
            "viaje_id": viaje.id,
            "message": "Buscando chofer disponible."
        })

    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)