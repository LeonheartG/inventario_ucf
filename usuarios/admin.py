# usuarios/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html
from .models import Rol, Departamento, PerfilUsuario, LogActividad


# Inline para mostrar el perfil en la página de usuario
class PerfilUsuarioInline(admin.StackedInline):
    model = PerfilUsuario
    can_delete = False
    verbose_name_plural = 'Perfil de Usuario'
    fields = ('departamento', 'rol', 'telefono', 'foto')
    extra = 0


# Extender el UserAdmin para incluir el perfil
class UserAdmin(BaseUserAdmin):
    inlines = (PerfilUsuarioInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'get_departamento',
                    'get_rol', 'is_staff', 'date_joined')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'date_joined',
                   'perfil__departamento', 'perfil__rol')

    def get_departamento(self, obj):
        try:
            return obj.perfil.departamento.nombre if obj.perfil.departamento else 'Sin asignar'
        except PerfilUsuario.DoesNotExist:
            return 'Sin perfil'
    get_departamento.short_description = 'Departamento'

    def get_rol(self, obj):
        try:
            if obj.perfil.rol:
                return obj.perfil.rol.nombre
            return 'Sin rol'
        except PerfilUsuario.DoesNotExist:
            return 'Sin perfil'
    get_rol.short_description = 'Rol'


# Re-registrar UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(Rol)
class RolAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descripcion')
    search_fields = ('nombre', 'descripcion')
    ordering = ('nombre',)


@admin.register(Departamento)
class DepartamentoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'ubicacion', 'responsable')
    list_filter = ('ubicacion',)
    search_fields = ('nombre', 'descripcion', 'ubicacion')
    ordering = ('nombre',)


@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ('get_usuario_info', 'departamento',
                    'rol', 'fecha_registro')
    list_filter = ('departamento', 'rol', 'fecha_registro')
    search_fields = ('usuario__username', 'usuario__first_name', 'usuario__last_name',
                     'usuario__email')
    readonly_fields = ('fecha_registro', 'ultimo_acceso')
    ordering = ('-fecha_registro',)

    def get_usuario_info(self, obj):
        user = obj.usuario
        nombre_completo = user.get_full_name()
        if nombre_completo:
            return f"{user.username} ({nombre_completo})"
        return user.username
    get_usuario_info.short_description = 'Usuario'


@admin.register(LogActividad)
class LogActividadAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'accion', 'fecha', 'ip')
    list_filter = ('accion', 'fecha', 'usuario')
    search_fields = ('usuario__username', 'accion', 'detalles', 'ip')
    readonly_fields = ('usuario', 'accion', 'fecha', 'detalles', 'ip')
    ordering = ('-fecha',)
    date_hierarchy = 'fecha'

    def has_add_permission(self, request):
        """No permitir agregar logs manualmente"""
        return False

    def has_change_permission(self, request, obj=None):
        """No permitir editar logs"""
        return False


# Personalizar el título del admin
admin.site.site_header = 'Administración - Sistema UCF'
admin.site.site_title = 'Admin UCF'
admin.site.index_title = 'Panel de Administración del Sistema de Gestión UCF'
