from django.contrib import admin
from django.urls import path, re_path
from django.views.generic import TemplateView
from Taxis import views
from Taxis import api_views

urlpatterns = [
    # Panel de Administración propio de Django

    # APIs PARA APP ANDROID Y SISTEMA DE UBICACIÓN
    path('api/chofer/ubicacion/', views.actualizar_ubicacion_chofer, name='actualizar_ubicacion_chofer'),
    path('api/admin/choferes-mapa/', views.api_choferes_activos_mapa, name='api_choferes_activos_mapa'),
    
    path('api/login/', api_views.api_login, name='api_login'),
    path('api/registro/', api_views.api_registro_cliente, name='api_registro_cliente'),
    path('api/registro/chofer/', api_views.api_registro_chofer, name='registro_usuario_o_chofer'),
    path('api/chofer/modalidad/', api_views.api_cambiar_modalidad_chofer, name='api_cambiar_modalidad_chofer'),
    path('api/viaje/solicitar/', api_views.api_solicitar_viaje_especial, name='api_solicitar_viaje_especial'),

    # ENDPOINTS API JSON UTILIZADOS POR EL FRONTEND EN REACT
    path('api/web/login/', views.api_web_login, name='api_web_login'),
    path('api/web/choferes-activos/', views.api_choferes_activos_mapa, name='api_web_choferes_activos_mapa'),
    path('api/web/gestion-choferes/', views.api_gestion_choferes, name='api_gestion_choferes'),
    path('api/web/roles/', views.api_roles, name='api_roles'),

    re_path(r'^.*$', TemplateView.as_view(template_name='taxis/react_base.html')),
]
#