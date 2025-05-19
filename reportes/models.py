from django.db import models
from django.contrib.auth.models import User


class Reporte(models.Model):
    TIPO_CHOICES = [
        ('inventario', 'Inventario'),
        ('mantenimiento', 'Mantenimiento'),
        ('diagnostico', 'Diagnóstico'),
        ('obsolescencia', 'Obsolescencia'),
        ('personalizado', 'Personalizado'),
    ]
    FORMATO_CHOICES = [
        ('pdf', 'PDF'),
        ('csv', 'CSV'),
        ('excel', 'Excel'),
    ]

    nombre = models.CharField(max_length=200)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    descripcion = models.TextField(blank=True, null=True)
    usuario = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='reportes')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    parametros = models.JSONField(blank=True, null=True)
    formato = models.CharField(
        max_length=10, choices=FORMATO_CHOICES, default='pdf')
    archivo = models.FileField(upload_to='reportes/', blank=True, null=True)

    def __str__(self):
        return f"{self.nombre} ({self.get_tipo_display()})"

    class Meta:
        verbose_name = "Reporte"
        verbose_name_plural = "Reportes"
        ordering = ['-fecha_creacion']


class ConfiguracionDashboard(models.Model):
    usuario = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='config_dashboard')
    widgets = models.JSONField()
    layout = models.JSONField()
    actualizado = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Configuración Dashboard de {self.usuario.username}"

    class Meta:
        verbose_name = "Configuración de Dashboard"
        verbose_name_plural = "Configuraciones de Dashboard"
