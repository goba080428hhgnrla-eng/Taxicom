from .models import Notificacion

def enviar_notificacion(usuario, tipo, mensaje):
    """
    Crea un registro en la tabla Notificacion para un usuario.
    """
    return Notificacion.objects.create(
        usuario=usuario,
        tipo=tipo,
        mensaje=mensaje
    )