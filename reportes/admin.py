from django.contrib import admin
from .models import Reporte, ConfiguracionDashboard


@admin.register(Reporte)
class ReporteAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'tipo', 'usuario', 'fecha_creacion', 'formato')
    list_filter = ('tipo', 'formato', 'fecha_creacion')
    search_fields = ('nombre', 'descripcion')
    readonly_fields = ('fecha_creacion', 'archivo')
    autocomplete_fields = ['usuario']


@admin.register(ConfiguracionDashboard)
class ConfiguracionDashboardAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'actualizado')
    search_fields = ('usuario__username',)
    readonly_fields = ('actualizado',)
    autocomplete_fields = ['usuario']
