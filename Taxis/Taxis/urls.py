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
from django.views.decorators.csrf import csrf_exempt

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

    # NOTA: les faltaba el prefijo 'api/v1/' -- estaban registradas como
    # '/choferes/...' en vez de '/api/v1/choferes/...', por eso el cliente
    # (que si le pega a la URL con el prefijo) nunca encontraba coincidencia
    # y caia en el comodin de React de hasta abajo.
    path(
        'api/v1/choferes/cambiar-modalidad/',
        csrf_exempt(CambiarModalidadChoferView.as_view()),
        name='cambiar-modalidad'
    ),
    path(
        'api/v1/choferes/ubicacion/',
        csrf_exempt(ActualizarUbicacionView.as_view()),
        name='actualizar-ubicacion'
    ),
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
    # Comodin de React -- SIEMPRE al final. Cualquier ruta nueva
    # que agregues arriba de esta linea funciona; cualquiera que
    # agregues abajo, nunca se va a alcanzar.
    # ==========================================================
    re_path(r'^(?!static/).*$', TemplateView.as_view(template_name='taxis/react_base.html')),
]