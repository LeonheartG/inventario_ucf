from django.contrib import admin
from .models import Local, EquipamientoLocal


class EquipamientoLocalInline(admin.TabularInline):
    model = EquipamientoLocal
    extra = 1
    autocomplete_fields = ['hardware']


@admin.register(Local)
class LocalAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'tipo', 'capacidad',
                    'ubicacion', 'departamento', 'estado')
    list_filter = ('tipo', 'estado', 'departamento')
    search_fields = ('nombre', 'ubicacion', 'descripcion')
    inlines = [EquipamientoLocalInline]
    autocomplete_fields = ['departamento']


@admin.register(EquipamientoLocal)
class EquipamientoLocalAdmin(admin.ModelAdmin):
    list_display = ('local', 'hardware', 'fecha_asignacion', 'estado')
    list_filter = ('estado', 'local')
    search_fields = ('local__nombre', 'hardware__activo__nombre')
    autocomplete_fields = ['local', 'hardware']
