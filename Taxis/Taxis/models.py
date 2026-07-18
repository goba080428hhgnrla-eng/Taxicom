from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
import bcrypt # Usaremos bcrypt para encriptar contraseñas de forma segura

from django.contrib.auth.hashers import make_password, check_password

class PerfilUsuario(models.Model):
    # Identificador único explícito (opcional, al estilo de tu referencia)
    id_usuario = models.AutoField(primary_key=True)
    
    # Credenciales e información base propia
    username = models.CharField(max_length=50, unique=True)
    password_hash = models.CharField(max_length=255) # Reemplaza a 'password' de tu referencia
    nombre = models.CharField(max_length=100, blank=True, null=True)
    apellido = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField(unique=True)
    telefono = models.CharField(max_length=15, blank=True, null=True)
    foto = models.ImageField(upload_to='perfiles/', null=True, blank=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    # ROLES CONTROLADOS POR BOOLEANOS (Estilo de tu referencia adaptado a Taxis)
    es_cliente = models.BooleanField(default=True)   # Equivalente a es_comprador
    es_chofer = models.BooleanField(default=False)   # Equivalente a es_repartidor
    es_admin = models.BooleanField(default=False)    # Equivalente a es_admin

    # Estado y Geolocalización en tiempo real
    estado_conexion = models.CharField(max_length=100, blank=True, null=True) # Disponible, desconectado, etc.
    latitud = models.FloatField(null=True, blank=True)
    longitud = models.FloatField(null=True, blank=True)
    fcm_token = models.TextField(blank=True, null=True)

    # =========================================================
    # PROPIEDAD DINÁMICA DE ROL (Traduce booleanos a texto)
    # =========================================================
    @property
    def rol(self):
        """Devuelve el rol en texto analizando los booleanos internos"""
        if getattr(self, 'es_admin', False):
            return 'admin'
        elif getattr(self, 'es_chofer', False):
            return 'chofer'
        return 'cliente'

    @rol.setter
    def rol(self, value):
        """Permite asignar texto perfil.rol = 'chofer' y actualiza los booleanos automáticamente"""
        if value in ['admin', 'administrador']:
            self.es_admin = True
            self.es_cliente = False
            self.es_chofer = False
        elif value in ['chofer', 'taxista', 'repartidor']:
            self.es_admin = False
            self.es_cliente = False
            self.es_chofer = True
        else: # cliente / comprador
            self.es_admin = False
            self.es_cliente = True
            self.es_chofer = False

    # =========================================================
    # ENCRIPTACIÓN AUTOMÁTICA AL GUARDAR
    # =========================================================
    def save(self, *args, **kwargs):
        """Detecta si la contraseña es plana y la encripta usando el hash nativo de Django antes de guardar"""
        if not self.password_hash.startswith('pbkdf2_'):
            self.password_hash = make_password(self.password_hash)
        super().save(*args, **kwargs)

    # =========================================================
    # MÉTODO MANUAL DE COMPROBACIÓN (Para tus Vistas/Login)
    # =========================================================
    def check_password(self, raw_password):
        """Valida la contraseña ingresada contra el hash almacenado"""
        return check_password(raw_password, self.password_hash)

    class Meta:
        verbose_name = 'Perfil de Usuario'
        verbose_name_plural = 'Perfiles de Usuarios'
        ordering = ['-fecha_registro']

    def __str__(self):
        return f"{self.nombre or ''} {self.apellido or ''} ({self.rol.upper()})"

# =========================================================
# CONTROL DE VEHÍCULOS
# =========================================================
class Vehiculo(models.Model):
    marca = models.CharField(max_length=50)
    modelo = models.CharField(max_length=50)
    anio = models.IntegerField()
    placas = models.CharField(max_length=20, unique=True)
    total_asientos = models.IntegerField(default=4)
    tiene_cajuela = models.BooleanField(default=True)
    sketchfab_model_id = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.marca} {self.modelo} - Placas: {self.placas}"


# =========================================================
# CONTROL DE CHOFERES (Apunta a nuestro PerfilUsuario)
# =========================================================
class Chofer(models.Model):
    ESTADOS = (
        ('pendiente', 'Pendiente de Aprobación'),
        ('activo', 'Activo / Libre'),
        ('en_ruta', 'En Ruta Fija'),
        ('inactivo', 'Inactivo'),
    )
    perfil = models.OneToOneField(PerfilUsuario, on_delete=models.CASCADE, related_name='chofer_datos')
    vehiculo = models.OneToOneField(Vehiculo, on_delete=models.SET_NULL, null=True, blank=True, related_name='chofer_actual')
    estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')
    grupo_rol = models.CharField(max_length=20, blank=True, null=True)
    asientos_disponibles = models.IntegerField(default=4)
    latitud = models.FloatField(default=0.0)
    longitud = models.FloatField(default=0.0)
    ultima_actualizacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Chofer: {self.perfil.nombre} ({self.estado})"


# =========================================================
# GESTIÓN DE ROLES Y VIAJES (Iguales, apuntando a PerfilUsuario)
# =========================================================
class RolDia(models.Model):
    grupo = models.CharField(max_length=20)
    dia_semana = models.CharField(max_length=15)

    class Meta:
        unique_together = ('grupo', 'dia_semana')


class Viaje(models.Model):
    ESTADOS_VIAJE = (
        ('solicitado', 'Buscando Chofer'),
        ('aceptado', 'Chofer en camino'),
        ('en_curso', 'En viaje'),
        ('terminado', 'Viaje Concluido'),
        ('cancelado', 'Viaje Cancelado'),
    )
    cliente = models.ForeignKey(PerfilUsuario, on_delete=models.CASCADE, related_name='viajes_solicitados')
    chofer = models.ForeignKey(Chofer, on_delete=models.SET_NULL, null=True, blank=True, related_name='viajes_atendidos')
    origen_lat = models.FloatField()
    origen_lng = models.FloatField()
    origen_direccion = models.CharField(max_length=255, blank=True)
    destino_lat = models.FloatField()
    destino_lng = models.FloatField()
    destino_direccion = models.CharField(max_length=255, blank=True)
    asientos_solicitados = models.IntegerField(default=1)
    requiere_cajuela = models.BooleanField(default=False)
    estado = models.CharField(max_length=20, choices=ESTADOS_VIAJE, default='solicitado')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    calificacion = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(5)])