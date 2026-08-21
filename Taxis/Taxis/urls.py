from django.urls import path, re_path

from django.views.generic import TemplateView

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
    DetalleChoferView,
)

from Taxis.api.v1.viajes import (
    SolicitarViajeView,
    CalificarViajeView,
    MisViajesView,
)

from Taxis.api.v1.roles import (
    RolesConfigView,
    ConfirmarPagoEfectivoView,
)

from Taxis.api.v1.rutas import (
    RutasListCreateView,
    RutaDetailView,
    SolicitarColectivoView,
    RutasClienteView,
)


urlpatterns = [

    # =====================================================
    # AUTENTICACIÓN
    # =====================================================

    path(
        "api/v1/auth/login/",
        LoginView.as_view(),
        name="api_login_v1"
    ),

    path(
        "api/v1/auth/registro/",
        RegistroClienteView.as_view(),
        name="api_registro_v1"
    ),

    path(
        "api/v1/auth/promover-chofer/",
        PromocionarAChoferView.as_view(),
        name="api_promover_chofer_v1"
    ),

    path(
        "api/v1/auth/registro-chofer/",
        RegistroChoferDesdeCeroView.as_view(),
        name="api_registro_chofer_v1"
    ),

    path(
        "api/v1/auth/refresh/",
        TokenRefreshView.as_view(),
        name="api_token_refresh"
    ),


    # =====================================================
    # CHOFER
    # =====================================================

    path(
        "api/v1/choferes/cambiar-modalidad/",
        CambiarModalidadChoferView.as_view(),
        name="cambiar_modalidad"
    ),

    path(
        "api/v1/choferes/ubicacion/",
        ActualizarUbicacionView.as_view(),
        name="actualizar_ubicacion"
    ),

    path(
        "api/v1/choferes/pagar-rol/",
        PagarRolView.as_view(),
        name="api_pagar_rol_v1"
    ),


    # =====================================================
    # VIAJES
    # =====================================================

    path(
        "api/v1/viajes/solicitar/",
        SolicitarViajeView.as_view(),
        name="api_solicitar_viaje_v1"
    ),

    path(
        "api/v1/viajes/calificar/",
        CalificarViajeView.as_view(),
        name="api_calificar_viaje_v1"
    ),

    path(
        "api/v1/viajes/mios/",
        MisViajesView.as_view(),
        name="api_mis_viajes_v1"
    ),


    # =====================================================
    # COLECTIVOS
    # =====================================================

    path(
        "api/v1/viajes/colectivo/solicitar/",
        SolicitarColectivoView.as_view(),
        name="api_solicitar_colectivo_v1"
    ),

    path(
        "api/v1/viajes/colectivo/rutas/",
        RutasClienteView.as_view(),
        name="api_rutas_cliente_v1"
    ),


    # =====================================================
    # ADMIN
    # =====================================================

    path(
        "api/v1/admin/choferes/",
        ListaChoferesView.as_view(),
        name="api_lista_choferes_v1"
    ),

    path(
        "api/v1/admin/choferes/gestionar/",
        GestionChoferView.as_view(),
        name="api_gestion_chofer_v1"
    ),

    path(
        "api/v1/admin/choferes/mapa/",
        MapaChoferesActivosView.as_view(),
        name="api_mapa_choferes_v1"
    ),

    path(
        "api/v1/admin/usuarios/",
        ListaUsuariosView.as_view(),
        name="api_lista_usuarios_v1"
    ),


    # =====================================================
    # ROLES
    # =====================================================

    path(
        "api/v1/admin/roles/",
        RolesConfigView.as_view(),
        name="api_roles_config_v1"
    ),

    #path(
     #   "api/v1/admin/roles/guardar-regla/",
      #  GuardarReglaRolView.as_view(),
       # name="api_guardar_regla_v1"
    #),

    #path(
     #   "api/v1/admin/roles/eliminar-grupo/",
      #  EliminarGrupoRolView.as_view(),
       # name="api_eliminar_grupo_v1"
    #),

    #path(
     #   "api/v1/admin/roles/asignar-chofer/",
      #  AsignarChoferGrupoView.as_view(),
       # name="api_asignar_chofer_v1"
    #),


    # =====================================================
    # RUTAS
    # =====================================================

    path("api/v1/admin/rutas/", RutasListCreateView.as_view(), name="api_rutas_v1"),
    path("api/v1/rutas", RutasClienteView.as_view(), name="api_rutas_si"),
    path("api/v1/admin/rutas/<int:ruta_id>/", RutaDetailView.as_view(), name="api_ruta_detalle_v1"),
    #path("api/v1/admin/rutas/<int:ruta_id>/agregar-chofer/", AgregarChoferRutaView.as_view(), name="api_agregar_chofer_ruta_v1"),
    #path("api/v1/admin/rutas/<int:ruta_id>/quitar-chofer/", QuitarChoferRutaView.as_view(), name="api_quitar_chofer_ruta_v1"),
    path('api/v1/admin/roles/config/', RolesConfigView.as_view(), name='roles_config'),
    
    # Único botón manual que usará el admin
    path('api/v1/admin/roles/confirmar-pago/', ConfirmarPagoEfectivoView.as_view(), name='roles_confirmar_pago'),
    
    path('api/v1/admin/choferes/<int:chofer_id>/', DetalleChoferView.as_view(), name='admin_detalle_chofer'),
    # =====================================================
    # REACT
    # SIEMPRE AL FINAL
    # =====================================================
    re_path(r'^(?!static/).*$', TemplateView.as_view(template_name='taxis/react_base.html')),
]