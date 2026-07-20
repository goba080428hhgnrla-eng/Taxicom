"""
URL configuration for Taxicom project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from Taxis import views
from Taxis import api_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home_publico, name='home_publico'),
    path('login/', views.login_personalizado, name='login_personalizado'),
    path('logout/', views.logout_personalizado, name='logout_personalizado'),
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('dashboard/choferes/', views.gestion_choferes, name='gestion_choferes'),
    path('dashboard/roles/', views.asignar_roles, name='asignar_roles'),
    
    # NUEVA RUTA PARA TU TABLA INDEPENDIENTE DE INTEGRANTES
    path('dashboard/usuarios/', views.lista_usuarios, name='lista_usuarios'),
    path('dashboard/roles/', views.asignar_roles, name='asignar_roles'),
    
    
    
    #Apis de android
    
    path('api/login/', api_views.api_login, name='api_login'),
    path('api/registro/', api_views.api_registro_cliente, name='api_registro_cliente'),
    path('api/registro/chofer/', api_views.registro_usuario_o_chofer, name='registro_usuario_o_chofer'),
    path('api/chofer/modalidad/', api_views.api_cambiar_modalidad_chofer, name='api_cambiar_modalidad_chofer'),
    path('api/viaje/solicitar/', api_views.api_solicitar_viaje_especial, name='api_solicitar_viaje_especial'),
]
