from django.urls import path, re_path
from django.views.generic import TemplateView
from Taxis import views, api_views

from rest_framework_simplejwt.views import TokenRefreshView

from Taxis.api.v1.auth import (
    LoginView,
    RegistroClienteView,
    PromocionarAChoferView,
    RegistroChoferDesdeCeroView,
)
from Taxis.api.v1.choferes import (
    CambiarModalidadChoferView,
    ActualizarUbicacionView,
    PagarRolView,
)
from Taxis.api.v1.admin_panel import (
    ListaChoferesView,
    GestionChoferView,
    ListaUsuariosView,
    MapaChoferesActivosView,
)
from Taxis.api.v1.viajes import SolicitarViajeView, CalificarViajeView, MisViajesView
from Taxis.api.v1.roles import (
    RolesConfigView,
    GuardarReglaRolView,
    EliminarGrupoRolView,
    AsignarChoferGrupoView,
)

urlpatterns = [
    # ==========================================================
    # API v1 (DRF + JWT) -- lo nuevo, esto es lo que deben usar
    # React y la app Android de aqui en adelante.
    # ==========================================================
    path("api/v1/auth/login/", LoginView.as_view(), name="api_login_v1"),
    path("api/v1/auth/registro/", RegistroClienteView.as_view(), name="api_registro_v1"),
    path("api/v1/auth/promover-chofer/", PromocionarAChoferView.as_view(), name="api_promover_chofer_v1"),
    path("api/v1/auth/registro-chofer/", RegistroChoferDesdeCeroView.as_view(), name="api_registro_chofer_v1"),
    path("api/v1/auth/refresh/", TokenRefreshView.as_view(), name="api_token_refresh"),

    path("api/v1/choferes/modalidad/", CambiarModalidadChoferView.as_view(), name="api_modalidad_v1"),
    path("api/v1/choferes/ubicacion/", ActualizarUbicacionView.as_view(), name="api_ubicacion_v1"),
    path("api/v1/choferes/pagar-rol/", PagarRolView.as_view(), name="api_pagar_rol_v1"),

    path("api/v1/viajes/solicitar/", SolicitarViajeView.as_view(), name="api_solicitar_viaje_v1"),
    path("api/v1/viajes/calificar/", CalificarViajeView.as_view(), name="api_calificar_viaje_v1"),
    path("api/v1/viajes/mios/", MisViajesView.as_view(), name="api_mis_viajes_v1"),

    path("api/v1/admin/choferes/", ListaChoferesView.as_view(), name="api_lista_choferes_v1"),
    path("api/v1/admin/choferes/gestionar/", GestionChoferView.as_view(), name="api_gestion_chofer_v1"),
    path("api/v1/admin/choferes/mapa/", MapaChoferesActivosView.as_view(), name="api_mapa_choferes_v1"),
    path("api/v1/admin/usuarios/", ListaUsuariosView.as_view(), name="api_lista_usuarios_v1"),

    path("api/v1/admin/roles/", RolesConfigView.as_view(), name="api_roles_config_v1"),
    path("api/v1/admin/roles/guardar-regla/", GuardarReglaRolView.as_view(), name="api_guardar_regla_v1"),
    path("api/v1/admin/roles/eliminar-grupo/", EliminarGrupoRolView.as_view(), name="api_eliminar_grupo_v1"),
    path("api/v1/admin/roles/asignar-chofer/", AsignarChoferGrupoView.as_view(), name="api_asignar_chofer_v1"),

    # ==========================================================
    # API viejas (sin auth por token, ya migradas arriba a v1).
    # Dejalas mientras terminas de mover React/Kotlin al v1, y
    # borralas cuando ya nadie las llame -- si las dos versiones
    # del mismo endpoint conviven, es facil que un cliente quede
    # pegado a la insegura por accidente.
    # ==========================================================
    path('api/chofer/ubicacion/', views.actualizar_ubicacion_chofer, name='actualizar_ubicacion_chofer'),
    path('api/admin/choferes-mapa/', views.api_choferes_activos_mapa, name='api_choferes_activos_mapa'),

    path('api/login/', api_views.api_login, name='api_login'),
    path('api/registro/', api_views.api_registro_cliente, name='api_registro_cliente'),
    path('api/registro/chofer/', api_views.api_registro_chofer, name='registro_usuario_o_chofer'),
    path('api/chofer/modalidad/', api_views.api_cambiar_modalidad_chofer, name='api_cambiar_modalidad_chofer'),
    path('api/viaje/solicitar/', api_views.api_solicitar_viaje_especial, name='api_solicitar_viaje_especial'),

    path('api/web/login/', views.api_web_login, name='api_web_login'),
    path('api/web/choferes-activos/', views.api_choferes_activos_mapa, name='api_web_choferes_activos_mapa'),
    path('api/web/gestion-choferes/', views.api_gestion_choferes, name='api_gestion_choferes'),
    path('api/web/roles/', views.api_roles, name='api_roles'),

    path('api/calificacion/crear/', api_views.api_crear_calificacion, name='api_crear_calificacion'),
    path('api/chofer/pagar-rol/', api_views.api_pagar_rol, name='api_pagar_rol'),

    # ==========================================================
    # Comodin de React -- SIEMPRE al final. Cualquier ruta nueva
    # que agregues arriba de esta linea funciona; cualquiera que
    # agregues abajo, nunca se va a alcanzar.
    # ==========================================================
    re_path(r'^(?!static/).*$', TemplateView.as_view(template_name='taxis/react_base.html')),
]