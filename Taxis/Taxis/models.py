from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.hashers import make_password, check_password
from .utils import enviar_notificacion


class PerfilUsuario(models.Model):
    id_usuario = models.AutoField(primary_key=True)
    username = models.CharField(max_length=50, unique=True, db_index=True)
    password_hash = models.CharField(max_length=255)
    nombre = models.CharField(max_length=100, blank=True, null=True)
    apellido = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField(unique=True, db_index=True)
    telefono = models.CharField(max_length=15, blank=True, null=True)
    foto = models.ImageField(upload_to='perfiles/', null=True, blank=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    # Roles controlados por booleanos
    es_cliente = models.BooleanField(default=True)
    es_chofer = models.BooleanField(default=False)
    es_admin = models.BooleanField(default=False)

    # Geolocalización general / Estado
    estado_conexion = models.CharField(max_length=100, blank=True, null=True)
    latitud = models.FloatField(null=True, blank=True)
    longitud = models.FloatField(null=True, blank=True)
    fcm_token = models.TextField(blank=True, null=True)

    @property
    def rol(self):
        if self.es_admin:
            return 'admin'
        elif self.es_chofer:
            return 'chofer'
        return 'cliente'

    @rol.setter
    def rol(self, value):
        if value in ['admin', 'administrador']:
            self.es_admin, self.es_cliente, self.es_chofer = True, False, False
        elif value in ['chofer', 'taxista', 'repartidor']:
            self.es_admin, self.es_cliente, self.es_chofer = False, False, True
        else:
            self.es_admin, self.es_cliente, self.es_chofer = False, True, False

    def save(self, *args, **kwargs):
        if not self.password_hash.startswith('pbkdf2_'):
            self.password_hash = make_password(self.password_hash)
        super().save(*args, **kwargs)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password_hash)

    class Meta:
        verbose_name = 'Perfil de Usuario'
        verbose_name_plural = 'Perfiles de Usuarios'
        ordering = ['-fecha_registro']

    def __str__(self):
        return f"{self.nombre or ''} {self.apellido or ''} ({self.rol.upper()})"
    
    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False


class Vehiculo(models.Model):
    marca = models.CharField(max_length=50)
    modelo = models.CharField(max_length=50)
    anio = models.IntegerField()
    placas = models.CharField(max_length=20, unique=True, db_index=True)
    total_asientos = models.IntegerField(default=4)
    tiene_cajuela = models.BooleanField(default=True)
    sketchfab_model_id = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.marca} {self.modelo} - Placas: {self.placas}"


class Chofer(models.Model):
    ESTADOS = (
        ('pendiente', 'Pendiente de Aprobación'),
        ('activo', 'Activo / Libre'),
        ('en_ruta', 'En Ruta Fija'),
        ('inactivo', 'Inactivo'),
    )
    perfil = models.OneToOneField(PerfilUsuario, on_delete=models.CASCADE, related_name='chofer_datos')
    vehiculo = models.OneToOneField(Vehiculo, on_delete=models.SET_NULL, null=True, blank=True, related_name='chofer_actual')
    base = models.ForeignKey('Base', on_delete=models.SET_NULL, null=True, blank=True, related_name='choferes')
    estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente', db_index=True)
    grupo_rol = models.CharField(max_length=20, blank=True, null=True)
    asientos_disponibles = models.IntegerField(default=4)
    
    # Índices optimizados para rastreo rápido de mapa
    latitud = models.FloatField(default=0.0, db_index=True)
    longitud = models.FloatField(default=0.0, db_index=True)
    ultima_actualizacion = models.DateTimeField(auto_now=True)


    def pagar_rol(self, monto):
        from django.utils import timezone
        from .models import PagoRol

        hoy = timezone.now().date()

        # verificar si ya pago
        if PagoRol.objects.filter(chofer=self, fecha_pago__date=hoy, estado='pagado').exists():
            return False  # Ya pago hoy, no puede pagar otra vez

        # Calcular los diasque debe 
        ultimo_pago = PagoRol.objects.filter(chofer=self, estado='pagado').order_by('-fecha_pago').first()
        
        if ultimo_pago:
            #dias trancurridos desde el ultimo pago
            dias_deuda = (hoy - ultimo_pago.fecha_pago.date()).days
        else:
            # Si nunca ha pagado asumimos que debo por lo menos el de hoy
            dias_deuda = 1

        
        if dias_deuda <= 0: # por si la deusa es 0, no se hace nada
            return False

        # Calcular el costo total de la deuda
        #====dejo 150 por defecto

        costo_por_dia = 150.00
        total_adeudado = dias_deuda * costo_por_dia

        # Verificar que el monto que envio cubra la deuda total
        if monto < total_adeudado:
            return False  # no paga lo suficiente nose registra el pago 


        PagoRol.objects.create(
            chofer=self,
            monto=monto,
            estado='pagado'
        )

        # Si estaba inactivo, lo activamos
        if self.estado == 'inactivo':
            self.estado = 'activo'
            self.save()

        # Enviar notificacion de exito
        enviar_notificacion(
            usuario=self.perfil,
            tipo='pago_rol',
            mensaje=f'Has pagado tu rol por ${monto}. Deuda saldada.'
        )
        
        return True
    
    
    class Meta:
        verbose_name = 'Chofer'
        verbose_name_plural = 'Choferes'

    def __str__(self):
        return f"Chofer: {self.perfil.nombre} ({self.get_estado_display()})"


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
    estado = models.CharField(max_length=20, choices=ESTADOS_VIAJE, default='solicitado', db_index=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

class Ruta(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.nombre


class Base(models.Model):
    nombre = models.CharField(max_length=100)
    direccion = models.TextField()
    latitud = models.FloatField(default=0.0)
    longitud = models.FloatField(default=0.0)
    telefono = models.CharField(max_length=15, blank=True, null=True)
    
    def __str__(self):
        return self.nombre


class AdministradorBase(models.Model):
    perfil = models.OneToOneField(PerfilUsuario, on_delete=models.CASCADE, related_name='admin_base')
    base = models.ForeignKey(Base, on_delete=models.CASCADE, related_name='administradores')
    
    def __str__(self):
        return f"Admin de {self.base.nombre}"


class Parada(models.Model):
    nombre = models.CharField(max_length=100)
    latitud = models.FloatField()
    longitud = models.FloatField()
    direccion = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.nombre


class RutaParada(models.Model):
    ruta = models.ForeignKey(Ruta, on_delete=models.CASCADE)  # Ahora Ruta ya existe arriba
    parada = models.ForeignKey(Parada, on_delete=models.CASCADE)
    orden = models.IntegerField()

    class Meta:
        ordering = ['orden']


class Pago(models.Model):
    ESTADOS_PAGO = (
        ('pendiente', 'Pendiente'),
        ('pagado', 'Pagado'),
        ('rechazado', 'Rechazado'),
    )
    viaje = models.OneToOneField(Viaje, on_delete=models.CASCADE, related_name='pago')
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    metodo_pago = models.CharField(max_length=20, default='efectivo')
    estado = models.CharField(max_length=20, choices=ESTADOS_PAGO, default='pendiente')
    fecha_pago = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Pago Viaje #{self.viaje.id} - {self.monto}"


    #modelos faltantes

class Calificacion(models.Model):
    viaje = models.OneToOneField(Viaje, on_delete=models.CASCADE, related_name='calificacion')
    puntaje = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comentario = models.TextField(blank=True, null=True)
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Calificación #{self.id} - {self.puntaje} estrellas"


class ViajeEspecial(models.Model):
    TIPOS = (
        ('contratado', 'Servicio Contratado'),
        ('paquete', 'Paquete Turístico'),
        ('personalizado', 'Personalizado'),
    )
    ESTADOS = (
        ('solicitado', 'Solicitado'),
        ('aceptado', 'Aceptado'),
        ('finalizado', 'Finalizado'),
    )
    cliente = models.ForeignKey(PerfilUsuario, on_delete=models.CASCADE, related_name='viajes_especiales')
    chofer = models.ForeignKey(Chofer, on_delete=models.SET_NULL, null=True, blank=True)
    tipo = models.CharField(max_length=20, choices=TIPOS, default='contratado')
    origen = models.CharField(max_length=255)
    destino = models.CharField(max_length=255)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='solicitado')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    monto_total = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    pago = models.OneToOneField(Pago, on_delete=models.SET_NULL, null=True, blank=True, related_name='viaje_especial')
    def __str__(self):
        return f"Viaje Especial #{self.id} - {self.tipo}"


class Incomprobante(models.Model):
    pago = models.OneToOneField(Pago, on_delete=models.CASCADE, related_name='incomprobante')
    archivo = models.FileField(upload_to='comprobantes/', blank=True, null=True)  
    fecha_subida = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, default='pendiente')  # pendiente, verificado, rechazado
    
    def __str__(self):
        return f"Comprobante de pago #{self.pago.id}"




class Notificacion(models.Model):

    TIPOS = (
        ('asignacion_viaje', 'Asignación de Viaje'),
        ('pago_rol', 'Pago de Rol'),
        ('calificacion', 'Nueva Calificación'),
    )

    usuario = models.ForeignKey(PerfilUsuario, on_delete=models.CASCADE,
     related_name='notificaciones')
    tipo = models.CharField(max_length=20, choices=TIPOS)
    mensaje = models.TextField()
    leida = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.tipo} - {self.usuario.nombre}"

class PagoRol(models.Model):
    ESTADOS = (
        ('pendiente', 'Pendiente'),
        ('pagado', 'Pagado'),
    )
    chofer = models.ForeignKey(Chofer, on_delete=models.CASCADE, related_name='pagos_rol')
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_pago = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='pagado')
    
    def __str__(self):
        return f"Pago de rol - {self.chofer} - ${self.monto}"
    