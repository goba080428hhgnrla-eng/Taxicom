"""
Ubicacion: Taxis/Taxis/permissions.py

Permisos por rol. Asumen que authentication.py ya puso una instancia de
PerfilUsuario en request.user.
"""
from rest_framework.permissions import BasePermission


class EsCliente(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.es_cliente)


class EsChofer(BasePermission):

    message = "El usuario debe ser un chofer."

    def has_permission(
        self,
        request,
        view
    ):

        usuario = request.user

        if not usuario:
            return False

        if not usuario.is_authenticated:
            return False

        return bool(
            getattr(usuario, "es_chofer", False)
        )


class EsAdmin(BasePermission):
    """Cualquier admin, sin distinguir base."""
    def has_permission(self, request, view):
        return bool(request.user and request.user.es_admin)


class EsElMismoChofer(BasePermission):
    """
    Un chofer solo puede actuar sobre SU PROPIO registro de Chofer.
    Uso en la vista: self.check_object_permissions(request, chofer_obj)
    """
    def has_object_permission(self, request, view, chofer_obj):
        return bool(
            request.user
            and request.user.es_chofer
            and hasattr(request.user, "chofer_datos")
            and request.user.chofer_datos.id == chofer_obj.id
        )


class EsAdminDeSuBase(BasePermission):
    """
    Restringe a admins que administran la Base a la que pertenece el objeto.
    Requiere AdministradorBase (ya existe en models.py) y que el objeto
    tenga un atributo/FK 'base'.
    """
    def has_object_permission(self, request, view, obj):
        if not (request.user and request.user.es_admin):
            return False
        if not hasattr(request.user, "admin_base"):
            return False
        base_del_objeto = getattr(obj, "base", None) or getattr(obj, "base_id", None)
        if base_del_objeto is None:
            return False
        return request.user.admin_base.base_id == getattr(
            base_del_objeto, "id", base_del_objeto
        )