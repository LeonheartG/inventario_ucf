# locales/admin.py
from django.contrib import admin
# Cambiar EquipamientoLocal por Equipamiento
from .models import Local, Equipamiento


@admin.register(Local)
class LocalAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'tipo', 'capacidad',
                    'ubicacion', 'departamento', 'estado')
    list_filter = ('tipo', 'estado', 'departamento')
    search_fields = ('nombre', 'ubicacion')


@admin.register(Equipamiento)  # Cambiar EquipamientoLocal por Equipamiento
class EquipamientoAdmin(admin.ModelAdmin):
    list_display = ('local', 'hardware', 'estado', 'fecha_asignacion')
    list_filter = ('estado', 'local', 'fecha_asignacion')
    search_fields = ('local__nombre', 'hardware__activo__nombre')
    autocomplete_fields = ['local', 'hardware']
