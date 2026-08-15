"""
Ubicacion: Taxis/Taxis/api/v1/auth.py

Login y registro (cliente + chofer), migrados a DRF + JWT.
Reemplazan api_login / api_registro_cliente / api_registro_chofer de
api_views.py.

Contrato de respuesta del login/registro (nuevo):
    {
        "access": "<jwt de corta duracion>",
        "refresh": "<jwt de larga duracion>",
        "usuario": { ...mismos campos que antes... }
    }
El cliente (React / Kotlin) manda el access token en cada request:
    Authorization: Bearer <access>
Ya NO se manda usuario_id/chofer_id/cliente_id en el body para identificar
quien hace la peticion.
"""
from django.db import transaction
from django.db.models import Q

from rest_framework import serializers, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.settings import api_settings

from ...models import PerfilUsuario, Vehiculo, Chofer


from ...models import PerfilUsuario, Vehiculo, Chofer


def _usuario_a_dict(usuario: PerfilUsuario) -> dict:
    chofer_id = None

    if usuario.es_chofer and hasattr(usuario, "chofer_datos"):
        chofer_id = usuario.chofer_datos.id

    return {
        "id_usuario": usuario.id_usuario,
        "chofer_id": chofer_id,
        "nombre": f"{usuario.nombre or ''} {usuario.apellido or ''}".strip(),
        "correo": usuario.email,
        "rol": usuario.rol,
        "es_cliente": usuario.es_cliente,
        "es_chofer": usuario.es_chofer,
        "es_admin": usuario.es_admin,
    }


def _emitir_tokens(usuario: PerfilUsuario) -> dict:
    refresh = RefreshToken.for_user(usuario)

    return {
        "access": str(refresh.access_token),
        "refresh": str(refresh),
    }


def _generar_username(correo: str) -> str:
    base_username = correo.split("@")[0]
    username = base_username
    contador = 1

    while PerfilUsuario.objects.filter(username=username).exists():
        username = f"{base_username}{contador}"
        contador += 1

    return username


class LoginSerializer(serializers.Serializer):
    correo_o_usuario = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        identificador = attrs["correo_o_usuario"].strip()
        password = attrs["password"]

        try:
            usuario = PerfilUsuario.objects.get(
                Q(username=identificador) | Q(email=identificador)
            )
        except PerfilUsuario.DoesNotExist:
            raise serializers.ValidationError({
                "correo_o_usuario": "El usuario no existe."
            })

        if not usuario.check_password(password):
            raise serializers.ValidationError({
                "password": "Contraseña incorrecta."
            })

        attrs["usuario"] = usuario
        return attrs


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        usuario = serializer.validated_data["usuario"]

        data = _emitir_tokens(usuario)
        data["usuario"] = _usuario_a_dict(usuario)

        return Response(data, status=status.HTTP_200_OK)


# ---------------------------------------------------------------------------
# REGISTRO DE CLIENTE
# ---------------------------------------------------------------------------

class RegistroClienteSerializer(serializers.Serializer):
    nombre = serializers.CharField()
    apellido = serializers.CharField(required=False, allow_blank=True, default="")
    correo = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    telefono = serializers.CharField(required=False, allow_blank=True, default="")

    def validate_correo(self, value):
        if PerfilUsuario.objects.filter(email=value).exists():
            raise serializers.ValidationError("El correo ya esta registrado.")
        return value


class RegistroClienteView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegistroClienteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        datos = serializer.validated_data

        with transaction.atomic():
            usuario = PerfilUsuario.objects.create(
                username=_generar_username(datos["correo"]),
                nombre=datos["nombre"],
                apellido=datos["apellido"],
                email=datos["correo"],
                password_hash=datos["password"],  # save() lo hashea
                telefono=datos["telefono"],
                es_cliente=True,
                es_chofer=False,
                es_admin=False,
            )

        data = _emitir_tokens(usuario)
        data["usuario"] = _usuario_a_dict(usuario)
        return Response(data, status=status.HTTP_201_CREATED)


# Taxis/Taxis/api/v1/auth.py

from rest_framework.parsers import MultiPartParser, FormParser

# ---------------------------------------------------------------------------
# PROMOCIONAR A CHOFER (Usuario Autenticado)
# ---------------------------------------------------------------------------

class PromocionarAChoferSerializer(serializers.Serializer):
    marca = serializers.CharField()
    modelo = serializers.CharField()
    anio = serializers.IntegerField()
    placas = serializers.CharField()
    total_asientos = serializers.IntegerField(default=4)
    tiene_cajuela = serializers.BooleanField(default=True)
    sketchfab_model_id = serializers.CharField(required=False, allow_blank=True, default="")
    
    # Archivos multimedia opcionales/requeridos
    foto = serializers.ImageField(required=False, allow_null=True)
    foto_licencia = serializers.ImageField(required=False, allow_null=True)

    def validate_placas(self, value):
        if Vehiculo.objects.filter(placas=value).exists():
            raise serializers.ValidationError("Un vehiculo con estas placas ya existe.")
        return value


class PromocionarAChoferView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser] # Permite recibir datos de multipart/form-data

    def post(self, request):
        serializer = PromocionarAChoferSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        datos = serializer.validated_data
        usuario = request.user

        with transaction.atomic():
            # Actualizamos la foto de perfil si fue provista
            if "foto" in request.FILES:
                usuario.foto = request.FILES["foto"]
            
            usuario.es_chofer = True
            usuario.save()

            vehiculo = Vehiculo.objects.create(
                marca=datos["marca"],
                modelo=datos["modelo"],
                anio=datos["anio"],
                placas=datos["placas"],
                total_asientos=datos["total_asientos"],
                tiene_cajuela=datos["tiene_cajuela"],
                sketchfab_model_id=datos["sketchfab_model_id"],
            )

            chofer, _creado = Chofer.objects.get_or_create(perfil=usuario)
            chofer.vehiculo = vehiculo
            chofer.estado = "pendiente"
            chofer.asientos_disponibles = datos["total_asientos"]
            
            # Guardamos la licencia si fue provista
            if "foto_licencia" in request.FILES:
                chofer.foto_licencia = request.FILES["foto_licencia"]
                
            chofer.save()

        return Response(
            {
                "status": "ok",
                "message": "Registro de chofer completado. Pendiente de aprobacion.",
                "chofer_id": chofer.id,
            },
            status=status.HTTP_201_CREATED,
        )


# ---------------------------------------------------------------------------
# REGISTRO DE CHOFER DESDE CERO
# ---------------------------------------------------------------------------

class RegistroChoferDesdeCeroSerializer(serializers.Serializer):
    nombre = serializers.CharField()
    apellido = serializers.CharField(required=False, allow_blank=True, default="")
    correo = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    telefono = serializers.CharField(required=False, allow_blank=True, default="")

    marca = serializers.CharField()
    modelo = serializers.CharField()
    anio = serializers.IntegerField()
    placas = serializers.CharField()
    total_asientos = serializers.IntegerField(default=4)
    tiene_cajuela = serializers.BooleanField(default=True)
    sketchfab_model_id = serializers.CharField(required=False, allow_blank=True, default="")

    # Imágenes
    foto = serializers.ImageField(required=False, allow_null=True)
    foto_licencia = serializers.ImageField(required=False, allow_null=True)

    def validate_correo(self, value):
        if PerfilUsuario.objects.filter(email=value).exists():
            raise serializers.ValidationError("El correo ya esta registrado.")
        return value

    def validate_placas(self, value):
        if Vehiculo.objects.filter(placas=value).exists():
            raise serializers.ValidationError("Un vehiculo con estas placas ya existe.")
        return value


class RegistroChoferDesdeCeroView(APIView):
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser] # Habilita multipart upload

    def post(self, request):
        serializer = RegistroChoferDesdeCeroSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        datos = serializer.validated_data

        with transaction.atomic():
            usuario = PerfilUsuario.objects.create(
                username=_generar_username(datos["correo"]),
                nombre=datos["nombre"],
                apellido=datos["apellido"],
                email=datos["correo"],
                password_hash=datos["password"],
                telefono=datos["telefono"],
                es_cliente=False,
                es_chofer=True,
                es_admin=False,
                foto=request.FILES.get("foto") # Guarda la foto de perfil directamente
            )

            vehiculo = Vehiculo.objects.create(
                marca=datos["marca"],
                modelo=datos["modelo"],
                anio=datos["anio"],
                placas=datos["placas"],
                total_asientos=datos["total_asientos"],
                tiene_cajuela=datos["tiene_cajuela"],
                sketchfab_model_id=datos["sketchfab_model_id"],
            )

            chofer = Chofer.objects.create(
                perfil=usuario,
                vehiculo=vehiculo,
                estado="pendiente",
                asientos_disponibles=datos["total_asientos"],
                foto_licencia=request.FILES.get("foto_licencia") # Guarda foto de licencia
            )

        data = _emitir_tokens(usuario)
        data["usuario"] = _usuario_a_dict(usuario)
        data["message"] = "Registro completado. Pendiente de aprobacion."
        return Response(data, status=status.HTTP_201_CREATED)