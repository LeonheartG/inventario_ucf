# usuarios/decorators.py
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import Http404


def rol_requerido(roles_permitidos):
    """
    Decorador que verifica si el usuario tiene uno de los roles permitidos

    Args:
        roles_permitidos: Lista de nombres de roles o string con un rol

    Usage:
        @rol_requerido(['Administrador', 'Supervisor'])
        @rol_requerido('Administrador')
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            # Convertir a lista si es string
            if isinstance(roles_permitidos, str):
                roles = [roles_permitidos]
            else:
                roles = roles_permitidos

            try:
                # Verificar si el usuario tiene perfil
                if not hasattr(request.user, 'perfil'):
                    messages.error(
                        request, 'Su cuenta no tiene un perfil asignado. Contacte al administrador.')
                    return redirect('dashboard')

                # Verificar si tiene rol asignado
                if not request.user.perfil.rol:
                    messages.error(
                        request, 'Su cuenta no tiene un rol asignado. Contacte al administrador.')
                    return redirect('dashboard')

                # Verificar si el rol está en los permitidos
                rol_usuario = request.user.perfil.rol.nombre
                if rol_usuario in roles:
                    return view_func(request, *args, **kwargs)
                else:
                    messages.error(
                        request, 'No tiene permisos para acceder a esta sección.')
                    return redirect('dashboard')

            except Exception as e:
                messages.error(
                    request, 'Error al verificar permisos. Contacte al administrador.')
                return redirect('dashboard')

        return wrapper
    return decorator


def admin_requerido(view_func):
    """
    Decorador para vistas que requieren rol de Administrador
    """
    return rol_requerido(['Administrador', 'Superadministrador'])(view_func)


def supervisor_o_admin_requerido(view_func):
    """
    Decorador para vistas que requieren rol de Supervisor o Administrador
    """
    return rol_requerido(['Administrador', 'Superadministrador', 'Supervisor'])(view_func)


def puede_ver_reportes(user):
    """
    Función auxiliar para verificar si un usuario puede ver reportes
    """
    try:
        if not hasattr(user, 'perfil') or not user.perfil.rol:
            return False

        roles_con_reportes = [
            'Administrador',
            'Superadministrador',
            'Supervisor',
            'Analista',
            'Coordinador'
        ]

        return user.perfil.rol.nombre in roles_con_reportes
    except:
        return False


def puede_ver_actividad(user):
    """
    Función auxiliar para verificar si un usuario puede ver actividad reciente
    """
    try:
        if not hasattr(user, 'perfil') or not user.perfil.rol:
            return False

        roles_con_actividad = [
            'Administrador',
            'Superadministrador',
            'Supervisor',
            'Coordinador'
        ]

        return user.perfil.rol.nombre in roles_con_actividad
    except:
        return False


def es_admin(user):
    """
    Función auxiliar para verificar si un usuario es administrador
    """
    try:
        if not hasattr(user, 'perfil') or not user.perfil.rol:
            return False

        return user.perfil.rol.nombre in ['Administrador', 'Superadministrador']
    except:
        return False


def tiene_permiso_inventario(user):
    """
    Función auxiliar para verificar permisos de inventario
    """
    try:
        if not hasattr(user, 'perfil') or not user.perfil.rol:
            return False

        roles_inventario = [
            'Administrador',
            'Superadministrador',
            'Supervisor',
            'Técnico',
            'Coordinador'
        ]

        return user.perfil.rol.nombre in roles_inventario
    except:
        return False


class PermissionMixin:
    """
    Mixin para CBVs que requieren verificación de permisos
    """
    roles_requeridos = []

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')

        if self.roles_requeridos:
            try:
                if not hasattr(request.user, 'perfil') or not request.user.perfil.rol:
                    messages.error(
                        request, 'Su cuenta no tiene permisos asignados.')
                    return redirect('dashboard')

                rol_usuario = request.user.perfil.rol.nombre
                if rol_usuario not in self.roles_requeridos:
                    messages.error(
                        request, 'No tiene permisos para acceder a esta sección.')
                    return redirect('dashboard')

            except Exception:
                messages.error(request, 'Error al verificar permisos.')
                return redirect('dashboard')

        return super().dispatch(request, *args, **kwargs)
