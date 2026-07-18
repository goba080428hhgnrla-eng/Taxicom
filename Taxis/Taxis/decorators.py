from django.shortcuts import redirect
from django.contrib import messages

def login_panel_required(view_func):
    """Decorador personalizado para proteger vistas usando las sesiones manuales"""
    def _wrapped_view(request, *args, **kwargs):
        if 'usuario_id' in request.session and request.session.get('usuario_rol') == 'admin':
            return view_func(request, *args, **kwargs)
        
        messages.error(request, "Por favor, inicia sesión como administrador para acceder.")
        return redirect('/login/') 
        
    return _wrapped_view