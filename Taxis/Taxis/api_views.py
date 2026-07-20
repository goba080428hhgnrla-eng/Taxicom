from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from .models import PerfilUsuario, Chofer, Viaje, Vehiculo
from django.db import transaction 
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
        
        
@csrf_exempt
def api_registro_chofer(request):
    """
    Endpoint transaccional para registrar un chofer junto con su vehículo y modelo 3D.
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)
        
    try:
        data = json.loads(request.body)
        
        # Datos del perfil
        nombre = data.get('nombre')
        apellido = data.get('apellido', '')
        email = data.get('correo') or data.get('email')
        password = data.get('password')
        telefono = data.get('telefono', '')
        
        # Datos del vehículo
        marca = data.get('marca')
        modelo = data.get('modelo')
        anio = data.get('anio')
        placas = data.get('placas')
        asientos = int(data.get('asientos', 4))
        cajuela = bool(data.get('cajuela', True))
        model_id_3d = data.get('sketchfab_model_id', '') # Guardamos el ID del modelo 3D seleccionado

        if not all([nombre, email, password, marca, modelo, placas]):
            return JsonResponse({'status': 'error', 'message': 'Faltan campos obligatorios para el registro'}, status=400)
            
        if PerfilUsuario.objects.filter(email=email).exists():
            return JsonResponse({'status': 'error', 'message': 'El correo ya está registrado'}, status=400)
            
        if Vehiculo.objects.filter(placas=placas).exists():
            return JsonResponse({'status': 'error', 'message': 'Un vehículo con estas placas ya existe'}, status=400)

        # Usamos una transacción para asegurar que todo se cree o nada se cree
        with transaction.atomic():
            # 1. Generar Username único
            username = email.split('@')[0]
            contador = 1
            username_original = username
            while PerfilUsuario.objects.filter(username=username).exists():
                username = f"{username_original}{contador}"
                contador += 1
            
            # 2. Crear Perfil de Usuario
            usuario = PerfilUsuario.objects.create(
                username=username,
                nombre=nombre,
                apellido=apellido,
                email=email,
                password_hash=password, # El save() lo enmascara automáticamente
                telefono=telefono,
                es_cliente=False,
                es_chofer=True,
                es_admin=False
            )
            
            # 3. Crear Vehículo
            vehiculo = Vehiculo.objects.create(
                marca=marca,
                modelo=modelo,
                anio=int(anio),
                placas=placas,
                total_asientos=asientos,
                tiene_cajuela=cajuela,
                sketchfab_model_id=model_id_3d
            )
            
            # 4. Crear Chofer vinculando ambos
            chofer = Chofer.objects.create(
                perfil=usuario,
                vehiculo=vehiculo,
                estado='pendiente', # Requiere validación física de papeles/admin
                asientos_disponibles=asientos
            )

        return JsonResponse({
            'status': 'ok',
            'message': 'Registro de chofer y vehículo completado exitosamente.',
            'id_usuario': usuario.id_usuario,
            'chofer_id': chofer.id
        })

    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'JSON inválido'}, status=400)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)        
    
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
from django.contrib.auth.hashers import make_password    
    
    
@csrf_exempt
def registro_chofer(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            perfil_id = data.get('perfil_id')

            # 1. Obtener o crear el perfil
            if perfil_id:
                perfil = PerfilUsuario.objects.get(id_usuario=perfil_id)
                perfil.rol = 'chofer'
                perfil.save()
            else:
                nombre = data.get('nombre')
                correo = data.get('correo')
                password = data.get('password')

                if not nombre or not correo or not password:
                    return JsonResponse({'error': 'Faltan datos personales'}, status=400)

                perfil = PerfilUsuario.objects.create(
                    username=correo,
                    email=correo,
                    nombre=nombre,
                    password_hash=password,
                    es_chofer=True,
                    es_cliente=False
                )

            # 2. Obtener datos del vehículo
            marca = data.get('marca')
            modelo = data.get('modelo')
            anio = data.get('anio')
            placas = data.get('placas')

            # Acepta tanto 'total_asientos' como 'asientos'
            asientos = data.get('total_asientos') or data.get('asientos') or 4

            # Acepta tanto 'tiene_cajuela' como 'cajuela'
            cajuela = data.get('tiene_cajuela') if data.get('tiene_cajuela') is not None else data.get('cajuela', True)

            if not marca or not modelo or not anio or not placas:
                return JsonResponse({'error': 'Faltan datos del vehiculo para realizar la promocion'}, status=400)

            # 3. Crear el vehículo en DB
            vehiculo = Vehiculo.objects.create(
                marca=marca,
                modelo=modelo,
                anio=int(anio),
                placas=placas,
                total_asientos=int(asientos),
                tiene_cajuela=bool(cajuela)
            )

            # 4. Asignar el vehículo al chofer
            chofer, created = Chofer.objects.get_or_create(perfil=perfil)
            chofer.vehiculo = vehiculo
            chofer.estado = 'activo'
            chofer.asientos_disponibles = int(asientos)
            chofer.save()

            return JsonResponse({'message': '¡Registro y promoción de chofer completada!'}, status=200)

        except PerfilUsuario.DoesNotExist:
            return JsonResponse({'error': 'El usuario no existe'}, status=404)
        except Exception as e:
            return JsonResponse({'error': f'Error en servidor: {str(e)}'}, status=500)

    return JsonResponse({'error': 'Método no permitido'}, status=405)