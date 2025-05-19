from django.db import models
from usuarios.models import Departamento
from inventario.models import Hardware


class Local(models.Model):
    TIPO_CHOICES = [
        ('laboratorio', 'Laboratorio'),
        ('aula', 'Aula'),
        ('sala', 'Sala de Conferencias'),
        ('oficina', 'Oficina'),
        ('otro', 'Otro'),
    ]
    ESTADO_CHOICES = [
        ('disponible', 'Disponible'),
        ('mantenimiento', 'En Mantenimiento'),
        ('ocupado', 'Ocupado'),
        ('fuera_servicio', 'Fuera de Servicio'),
    ]

    nombre = models.CharField(max_length=100)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    capacidad = models.IntegerField(default=0)
    ubicacion = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True, null=True)
    departamento = models.ForeignKey(
        Departamento, on_delete=models.CASCADE, related_name='locales')
    estado = models.CharField(
        max_length=20, choices=ESTADO_CHOICES, default='disponible')
    imagen = models.ImageField(upload_to='locales/', blank=True, null=True)
    notas = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.nombre} ({self.get_tipo_display()})"

    class Meta:
        verbose_name = "Local"
        verbose_name_plural = "Locales"


class EquipamientoLocal(models.Model):
    ESTADO_CHOICES = [
        ('operativo', 'Operativo'),
        ('defectuoso', 'Defectuoso'),
        ('mantenimiento', 'En Mantenimiento'),
    ]

    local = models.ForeignKey(
        Local, on_delete=models.CASCADE, related_name='equipamiento')
    hardware = models.ForeignKey(
        Hardware, on_delete=models.CASCADE, related_name='asignaciones')
    fecha_asignacion = models.DateField(auto_now_add=True)
    estado = models.CharField(
        max_length=20, choices=ESTADO_CHOICES, default='operativo')
    notas = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.hardware.activo.nombre} en {self.local.nombre}"

    class Meta:
        verbose_name = "Equipamiento de Local"
        verbose_name_plural = "Equipamientos de Locales"
        unique_together = ['local', 'hardware']
