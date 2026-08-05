
from django.contrib import admin
from django.urls import path, re_path
from django.views.generic import TemplateView
from Taxis import views
from Taxis import api_views

urlpatterns = [
    # Panel de Administración / Web
    path('admin/', admin.site.urls),
    path('', views.home_publico, name='home_publico'),
    path('login/', views.login_personalizado, name='login_personalizado'),
    path('logout/', views.logout_personalizado, name='logout_personalizado'),
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('dashboard/choferes/', views.gestion_choferes, name='gestion_choferes'),
    path('dashboard/roles/', views.asignar_roles, name='asignar_roles'),
    path('dashboard/usuarios/', views.lista_usuarios, name='lista_usuarios'),
    
    # APIs para Mapa y Ubicación
    path('api/chofer/ubicacion/', views.actualizar_ubicacion_chofer, name='actualizar_ubicacion_chofer'),
    path('api/admin/choferes-mapa/', views.api_choferes_activos_mapa, name='api_choferes_activos_mapa'),
    
    # APIs para App Android
    path('api/login/', api_views.api_login, name='api_login'),
    path('api/registro/', api_views.api_registro_cliente, name='api_registro_cliente'),
    path('api/registro/chofer/', api_views.api_registro_chofer, name='registro_usuario_o_chofer'), # Corregido
    path('api/chofer/modalidad/', api_views.api_cambiar_modalidad_chofer, name='api_cambiar_modalidad_chofer'),
    path('api/viaje/solicitar/', api_views.api_solicitar_viaje_especial, name='api_solicitar_viaje_especial'),
    
    
    
    # APIs de React 
    # API endpoints para el Panel Web React
    path('api/web/login/', views.api_web_login, name='api_web_login'),
    path('api/web/choferes-activos/', views.api_choferes_activos_mapa, name='api_choferes_activos_mapa'),
    path('api/web/gestion-choferes/',views.api_gestion_choferes, name='api_gestion_choferes'),
    path('api/web/roles/',views.api_roles, name='api_roles'),

    # Renderizador SPA de React
    re_path(r'^.*$', TemplateView.as_view(template_name='taxis/react_base.html')),
]