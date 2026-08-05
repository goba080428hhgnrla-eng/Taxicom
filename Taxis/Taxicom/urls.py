from django.contrib import admin
from django.urls import path, include, re_path
from django.views.generic import TemplateView
from Taxis import views, api_views 
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('admin_django/', admin.site.urls), 
    ##path('', views.home_publico, name='home_publico'),
    
    path('api/chofer/modalidad/', api_views.api_cambiar_modalidad_chofer, name='api_cambiar_modalidad'),
    path('api/viaje/especial/solicitar/', api_views.api_solicitar_viaje_especial, name='api_solicitar_especial'),
    
    path('', include('Taxis.urls')),
    
    re_path(r'^.*$', TemplateView.as_view(template_name='taxis/react_base.html')),
]
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)