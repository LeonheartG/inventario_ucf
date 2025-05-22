# usuarios/middleware.py
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse
from .decorators import puede_ver_reportes


class ReportesPermissionMiddleware:
    """
    Middleware que bloquea el acceso a URLs de reportes para usuarios sin permisos
    """

    def __init__(self, get_response):
        self.get_response = get_response

        # URLs que requieren permisos especiales
        self.protected_paths = [
            '/reportes/',
            '/export/',
        ]

    def __call__(self, request):
        # Verificar si la URL está protegida
        if any(request.path.startswith(path) for path in self.protected_paths):
            # Si no está autenticado, redirigir al login
            if not request.user.is_authenticated:
                return redirect('login')

            # Si está autenticado pero no tiene permisos
            if not puede_ver_reportes(request.user):
                messages.error(
                    request,
                    'No tiene permisos para acceder a la sección de reportes.'
                )
                return redirect('dashboard')

        response = self.get_response(request)
        return response


class RoleBasedAccessMiddleware:
    """
    Middleware más general para controlar acceso basado en roles
    """

    def __init__(self, get_response):
        self.get_response = get_response

        # Configuración de permisos por URL
        self.url_permissions = {
            '/admin/': ['Administrador', 'Superadministrador'],
            '/reportes/': ['Administrador', 'Superadministrador', 'Supervisor', 'Analista', 'Coordinador'],
            '/usuarios/admin/': ['Administrador', 'Superadministrador'],
        }

    def __call__(self, request):
        # Solo aplicar a usuarios autenticados
        if request.user.is_authenticated:

            # Verificar cada regla de URL
            for url_pattern, required_roles in self.url_permissions.items():
                if request.path.startswith(url_pattern):

                    # Verificar si el usuario tiene el rol requerido
                    user_role = self.get_user_role(request.user)

                    if user_role not in required_roles:
                        messages.error(
                            request,
                            f'Su rol "{user_role}" no tiene permisos para acceder a esta sección.'
                        )
                        return redirect('dashboard')

        response = self.get_response(request)
        return response

    def get_user_role(self, user):
        """Obtener el rol del usuario de forma segura"""
        try:
            if hasattr(user, 'perfil') and user.perfil.rol:
                return user.perfil.rol.nombre
            return 'Usuario Regular'
        except:
            return 'Usuario Regular'
