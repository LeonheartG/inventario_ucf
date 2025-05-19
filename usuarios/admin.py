from django.contrib import admin
from .models import Rol, Departamento, PerfilUsuario, LogActividad


@admin.register(Rol)
class RolAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descripcion')
    search_fields = ('nombre',)


@admin.register(Departamento)
class DepartamentoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'ubicacion', 'responsable')
    list_filter = ('ubicacion',)
    search_fields = ('nombre', 'descripcion')


@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'departamento', 'rol',
                    'fecha_registro', 'ultimo_acceso')
    list_filter = ('departamento', 'rol')
    search_fields = ('usuario__username',
                     'usuario__first_name', 'usuario__last_name')
    readonly_fields = ('fecha_registro', 'ultimo_acceso')


@admin.register(LogActividad)
class LogActividadAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'accion', 'fecha', 'ip')
    list_filter = ('usuario', 'fecha')
    search_fields = ('usuario__username', 'accion', 'detalles')
    readonly_fields = ('usuario', 'accion', 'fecha', 'detalles', 'ip')
