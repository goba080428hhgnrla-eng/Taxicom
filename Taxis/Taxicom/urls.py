from django.contrib import admin
from django.urls import path, include
from Taxis import views, api_views 

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home_publico, name='home_publico'),
    
    path('api/chofer/modalidad/', api_views.api_cambiar_modalidad_chofer, name='api_cambiar_modalidad'),
    path('api/viaje/especial/solicitar/', api_views.api_solicitar_viaje_especial, name='api_solicitar_especial'),
    
    path('', include('Taxis.urls')),
]