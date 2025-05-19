from django.contrib import admin
from .models import (
    Activo, Proveedor, Hardware, Software,
    Mantenimiento, Proceso, ActivoProceso
)


class HardwareInline(admin.StackedInline):
    model = Hardware
    can_delete = False


class SoftwareInline(admin.StackedInline):
    model = Software
    can_delete = False


@admin.register(Activo)
class ActivoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'tipo', 'estado', 'departamento',
                    'fecha_adquisicion', 'valor_adquisicion')
    list_filter = ('tipo', 'estado', 'departamento')
    search_fields = ('nombre', 'descripcion')
    date_hierarchy = 'fecha_adquisicion'
    readonly_fields = ('fecha_creacion', 'fecha_actualizacion')
    fieldsets = (
        ('Información Básica', {
            'fields': ('tipo', 'nombre', 'descripcion', 'imagen')
        }),
        ('Información Financiera', {
            'fields': ('valor_adquisicion', 'fecha_adquisicion')
        }),
        ('Ubicación', {
            'fields': ('departamento', 'ubicacion')
        }),
        ('Estado', {
            'fields': ('estado', 'fecha_baja', 'motivo_baja')
        }),
        ('Auditoría', {
            'fields': ('creado_por', 'fecha_creacion', 'actualizado_por', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )

    def get_inlines(self, request, obj=None):
        if obj:
            if obj.tipo == 'hardware':
                return [HardwareInline]
            elif obj.tipo == 'software':
                return [SoftwareInline]
        return []


@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'telefono', 'email')
    search_fields = ('nombre', 'email')


@admin.register(Hardware)
class HardwareAdmin(admin.ModelAdmin):
    list_display = ('activo', 'marca', 'modelo',
                    'numero_serie', 'fecha_garantia')
    list_filter = ('marca', 'proveedor')
    search_fields = ('activo__nombre', 'marca', 'modelo', 'numero_serie')
    autocomplete_fields = ['activo', 'proveedor']


@admin.register(Software)
class SoftwareAdmin(admin.ModelAdmin):
    list_display = ('activo', 'version', 'tipo_licencia',
                    'fecha_vencimiento', 'numero_licencias')
    list_filter = ('tipo_licencia', 'proveedor')
    search_fields = ('activo__nombre', 'version')
    autocomplete_fields = ['activo', 'proveedor']


@admin.register(Mantenimiento)
class MantenimientoAdmin(admin.ModelAdmin):
    list_display = ('activo', 'tipo', 'fecha_programada',
                    'fecha_realizacion', 'estado', 'responsable')
    list_filter = ('tipo', 'estado', 'fecha_programada')
    search_fields = ('activo__nombre', 'descripcion')
    date_hierarchy = 'fecha_programada'
    autocomplete_fields = ['activo', 'responsable']


class ActivoProcesoInline(admin.TabularInline):
    model = ActivoProceso
    extra = 1
    autocomplete_fields = ['activo']


@admin.register(Proceso)
class ProcesoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'tipo', 'departamento', 'responsable')
    list_filter = ('tipo', 'departamento')
    search_fields = ('nombre', 'descripcion')
    inlines = [ActivoProcesoInline]
    autocomplete_fields = ['departamento', 'responsable']


@admin.register(ActivoProceso)
class ActivoProcesoAdmin(admin.ModelAdmin):
    list_display = ('activo', 'proceso',
                    'nivel_importancia', 'fecha_asignacion')
    list_filter = ('nivel_importancia', 'proceso')
    search_fields = ('activo__nombre', 'proceso__nombre')
    autocomplete_fields = ['activo', 'proceso']
