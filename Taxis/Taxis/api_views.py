import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db.models import Q

from .models import PerfilUsuario, Chofer, Viaje, Vehiculo


@csrf_exempt
def api_login(request):
    """
    Endpoint de inicio de sesión compatible con la app Android (Volley/Retrofit).
    Soporta autenticación por correo o nombre de usuario en una sola consulta indexada.
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)

    try:
        data = json.loads(request.body)
        correo_o_user = data.get('correo') or data.get('username') or data.get('email')
        password = data.get('password')

        if not correo_o_user or not password:
            return JsonResponse({'status': 'error', 'message': 'Faltan credenciales'}, status=400)

        # Buscar usuario en DB por username O por email
        try:
            usuario = PerfilUsuario.objects.get(
                Q(username=correo_o_user) | Q(email=correo_o_user)
            )
        except PerfilUsuario.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'El usuario no existe'}, status=404)

        # Validar contraseña usando el método del modelo
        if not usuario.check_password(password):
            return JsonResponse({'status': 'error', 'message': 'Contraseña incorrecta'}, status=401)

        # Buscar datos adicionales si es chofer
        chofer_id = None
        if usuario.es_chofer and hasattr(usuario, 'chofer_datos'):
            chofer_id = usuario.chofer_datos.id

        return JsonResponse({
            "status": "ok",
            "id_usuario": usuario.id_usuario,
            "chofer_id": chofer_id,
            "nombre": f"{usuario.nombre or ''} {usuario.apellido or ''}".strip(),
            "correo": usuario.email,
            "rol": usuario.rol,
            "es_cliente": usuario.es_cliente,
            "es_chofer": usuario.es_chofer,
            "es_admin": usuario.es_admin
        }, status=200)

    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'JSON inválido'}, status=400)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@csrf_exempt
def api_registro_cliente(request):
    """
    Registro exclusivo de nuevos clientes desde Android.
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

        # Generar username único basado en el correo
        base_username = email.split('@')[0]
        username = base_username
        contador = 1
        while PerfilUsuario.objects.filter(username=username).exists():
            username = f"{base_username}{contador}"
            contador += 1

        with transaction.atomic():
            usuario = PerfilUsuario.objects.create(
                username=username,
                nombre=nombre,
                apellido=apellido,
                email=email,
                password_hash=password,  # El método save() del modelo genera el hash automático
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
        }, status=201)

    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'JSON inválido'}, status=400)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@csrf_exempt
def api_cambiar_modalidad_chofer(request):
    """
    Cambia el estado operativo del chofer (activo, en_ruta, inactivo).
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)

    try:
        data = json.loads(request.body)
        usuario_id = data.get('usuario_id') or data.get('id_usuario')
        nuevo_estado = data.get('estado')

        if not usuario_id or not nuevo_estado:
            return JsonResponse({'status': 'error', 'message': 'Faltan parámetros requeridos'}, status=400)

        chofer = get_object_or_404(Chofer, perfil__id_usuario=usuario_id)

        estados_validos = dict(Chofer.ESTADOS)
        if nuevo_estado not in estados_validos:
            return JsonResponse({'status': 'error', 'message': 'Estado inválido'}, status=400)

        chofer.estado = nuevo_estado
        chofer.save()

        return JsonResponse({
            'status': 'ok',
            'nuevo_estado': chofer.estado,
            'message': f'Estado actualizado a: {chofer.get_estado_display()}'
        }, status=200)

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@csrf_exempt
def api_solicitar_viaje_especial(request):
    """
    Crear una solicitud de viaje especial desde la App del Cliente.
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)

    try:
        data = json.loads(request.body)
        cliente_id = data.get('cliente_id') or data.get('id_usuario')

        if not cliente_id:
            return JsonResponse({'status': 'error', 'message': 'Identificador de cliente no proporcionado'}, status=400)

        cliente = get_object_or_404(PerfilUsuario, id_usuario=cliente_id)

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
            "message": "Solicitud creada. Buscando chofer disponible."
        }, status=201)

    except KeyError as k:
        return JsonResponse({'status': 'error', 'message': f'Falta el campo de coordenadas: {str(k)}'}, status=400)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@csrf_exempt
def api_registro_chofer(request):
    """
    Endpoint Unificado y Transaccional para Registro o Promoción de Chofer + Vehículo.
    Maneja 2 casos automáticamente:
      1. Si se envía 'perfil_id' o 'usuario_id': Promueve a un usuario existente.
      2. Si NO se envía ID: Registra un nuevo PerfilUsuario + Vehículo + Chofer.
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)

    try:
        data = json.loads(request.body)

        perfil_id = data.get('perfil_id') or data.get('usuario_id')

        # Datos del vehículo
        marca = data.get('marca')
        modelo = data.get('modelo')
        anio = data.get('anio')
        placas = data.get('placas')
        asientos = int(data.get('total_asientos') or data.get('asientos') or 4)
        cajuela = data.get('tiene_cajuela') if data.get('tiene_cajuela') is not None else data.get('cajuela', True)
        sketchfab_id = data.get('sketchfab_model_id', '')

        if not all([marca, modelo, anio, placas]):
            return JsonResponse({'status': 'error', 'message': 'Faltan datos obligatorios del vehículo'}, status=400)

        if Vehiculo.objects.filter(placas=placas).exists():
            return JsonResponse({'status': 'error', 'message': 'Un vehículo con estas placas ya existe'}, status=400)

        with transaction.atomic():
            # CASO A: Usuario ya existente (Promoción)
            if perfil_id:
                usuario = get_object_or_404(PerfilUsuario, id_usuario=perfil_id)
                usuario.es_chofer = True
                usuario.save()
            
            # CASO B: Usuario nuevo (Registro desde cero)
            else:
                nombre = data.get('nombre')
                apellido = data.get('apellido', '')
                email = data.get('correo') or data.get('email')
                password = data.get('password')
                telefono = data.get('telefono', '')

                if not all([nombre, email, password]):
                    return JsonResponse({'status': 'error', 'message': 'Faltan datos personales obligatorios'}, status=400)

                if PerfilUsuario.objects.filter(email=email).exists():
                    return JsonResponse({'status': 'error', 'message': 'El correo ya está registrado'}, status=400)

                # Username único
                base_username = email.split('@')[0]
                username = base_username
                contador = 1
                while PerfilUsuario.objects.filter(username=username).exists():
                    username = f"{base_username}{contador}"
                    contador += 1

                usuario = PerfilUsuario.objects.create(
                    username=username,
                    nombre=nombre,
                    apellido=apellido,
                    email=email,
                    password_hash=password,
                    telefono=telefono,
                    es_cliente=False,
                    es_chofer=True,
                    es_admin=False
                )

            # Crear el vehículo
            vehiculo = Vehiculo.objects.create(
                marca=marca,
                modelo=modelo,
                anio=int(anio),
                placas=placas,
                total_asientos=asientos,
                tiene_cajuela=bool(cajuela),
                sketchfab_model_id=sketchfab_id
            )

            # Crear o actualizar registro de Chofer vinculando Perfil y Vehículo
            chofer, _ = Chofer.objects.get_or_create(perfil=usuario)
            chofer.vehiculo = vehiculo
            chofer.estado = 'pendiente'  # Requiere aprobación del Administrador
            chofer.asientos_disponibles = asientos
            chofer.save()

        return JsonResponse({
            'status': 'ok',
            'message': 'Registro de chofer y vehículo completado exitosamente. Pendiente de aprobación.',
            'id_usuario': usuario.id_usuario,
            'chofer_id': chofer.id
        }, status=201)

    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'JSON inválido'}, status=400)
    except Exception as e:
        import traceback
        print(traceback.format_exc())

        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


# NUEVAS VISTAS PARA MODELOS AGREGADOS

@csrf_exempt
def api_crear_calificacion(request):
    """Endpoint para que el pasajero califique un viaje terminado.
    recibe viaje_id, puntaje, comentario 
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Metodo no permitido'}, status=405)

    try:
        data = json.loads(request.body)
        viaje_id = data.get('viaje_id')
        puntaje = data.get('puntaje')
        comentario = data.get('comentario', '')

        if not viaje_id or not puntaje:
            return JsonResponse({'status': 'error', 'message': 'Faltan viaje_id o puntaje'}, status=400)

        from .models import Viaje, Calificacion

        #buscar el viaje
        viaje = Viaje.objects.get(id=viaje_id)

        #verifica si ya tiene calificacion
        if hasattr(viaje, 'calificacion'):
            return JsonResponse({'status': 'error', 'message': 'Este viaje ya fue calificado'}, status=400)

        #crear la calificacion
        calificacion = Calificacion.objects.create(
            viaje=viaje,
            puntaje=int(puntaje),
            comentario=comentario
        )

        return JsonResponse({
            'status': 'ok',
            'calificacion_id': calificacion.id,
            'message': 'Calificación guardada exitosamente'
        }, status=201)

    except Viaje.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Viaje no encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@csrf_exempt
def api_pagar_rol(request):
    """endpoint para que el chofer pague su cuota diaria desde la app.
    recibe el chofer_id, monto
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)

    try:
        data = json.loads(request.body)
        chofer_id = data.get('chofer_id')
        monto = data.get('monto')

        if not chofer_id or not monto:
            return JsonResponse({'status': 'error', 'message': 'Faltan chofer_id o monto'}, status=400)

        from .models import Chofer

        #buscar el chofer
        chofer = Chofer.objects.get(id=chofer_id)

        # ejecutar la logica de pago
        resultado = chofer.pagar_rol(float(monto))

        if resultado:
            return JsonResponse({
                'status': 'ok',
                'message': 'Pago de rol realizado y chofer activado.'
            }, status=200)
        else:
            return JsonResponse({
                'status': 'error',
                'message': 'El chofer ya pagó el rol hoy.'
            }, status=400)

    except Chofer.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Chofer no encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)