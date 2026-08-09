

def enviar_notificacion(usuario, tipo, mensaje):
    from .models import Notificacion  
    return Notificacion.objects.create(
        usuario=usuario,
        tipo=tipo,
        mensaje=mensaje
    )