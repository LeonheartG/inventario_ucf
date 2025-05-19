from django.contrib import admin
from .models import Cuestionario, Pregunta, Diagnostico, Respuesta, IndicadorDiagnostico


class PreguntaInline(admin.TabularInline):
    model = Pregunta
    extra = 1


@admin.register(Cuestionario)
class CuestionarioAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'creado_por', 'fecha_creacion', 'activo')
    list_filter = ('activo', 'fecha_creacion')
    search_fields = ('titulo', 'descripcion')
    inlines = [PreguntaInline]
    autocomplete_fields = ['creado_por']


@admin.register(Pregunta)
class PreguntaAdmin(admin.ModelAdmin):
    list_display = ('texto', 'cuestionario', 'tipo', 'categoria', 'orden')
    list_filter = ('tipo', 'categoria', 'cuestionario')
    search_fields = ('texto', 'categoria')
    autocomplete_fields = ['cuestionario']


class RespuestaInline(admin.TabularInline):
    model = Respuesta
    extra = 1
    autocomplete_fields = ['pregunta']


class IndicadorDiagnosticoInline(admin.TabularInline):
    model = IndicadorDiagnostico
    extra = 1


@admin.register(Diagnostico)
class DiagnosticoAdmin(admin.ModelAdmin):
    list_display = ('departamento', 'responsable', 'fecha',
                    'nivel_general', 'cuestionario')
    list_filter = ('departamento', 'fecha')
    search_fields = ('departamento__nombre', 'observaciones')
    inlines = [RespuestaInline, IndicadorDiagnosticoInline]
    autocomplete_fields = ['departamento', 'responsable', 'cuestionario']
    readonly_fields = ('fecha',)


@admin.register(Respuesta)
class RespuestaAdmin(admin.ModelAdmin):
    list_display = ('diagnostico', 'pregunta', 'valor_numerico', 'valor_texto')
    list_filter = ('diagnostico',)
    search_fields = ('pregunta__texto', 'valor_texto')
    autocomplete_fields = ['diagnostico', 'pregunta']


@admin.register(IndicadorDiagnostico)
class IndicadorDiagnosticoAdmin(admin.ModelAdmin):
    list_display = ('diagnostico', 'nombre', 'valor')
    list_filter = ('diagnostico',)
    search_fields = ('nombre', 'descripcion')
    autocomplete_fields = ['diagnostico']
