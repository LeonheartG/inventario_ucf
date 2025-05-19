# inventario/models.py
from django.db import models
from django.contrib.auth.models import User
from usuarios.models import Departamento


class Activo(models.Model):
    TIPO_CHOICES = [
        ('hardware', 'Hardware'),
        ('software', 'Software'),
    ]
    ESTADO_CHOICES = [
        ('activo', 'Activo'),
        ('en_mantenimiento', 'En Mantenimiento'),
        ('obsoleto', 'Obsoleto'),
        ('baja', 'De Baja'),
    ]

    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True, null=True)
    fecha_adquisicion = models.DateField()
    valor_adquisicion = models.DecimalField(max_digits=10, decimal_places=2)
    estado = models.CharField(
        max_length=20, choices=ESTADO_CHOICES, default='activo')
    departamento = models.ForeignKey(
        Departamento, on_delete=models.CASCADE, related_name='activos')
    ubicacion = models.CharField(max_length=100, blank=True, null=True)
    imagen = models.ImageField(upload_to='activos/', blank=True, null=True)
    fecha_baja = models.DateField(blank=True, null=True)
    motivo_baja = models.TextField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    creado_por = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name='activos_creados')
    actualizado_por = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name='activos_actualizados')

    def __str__(self):
        return f"{self.nombre} ({self.get_tipo_display()})"

    class Meta:
        verbose_name = "Activo"
        verbose_name_plural = "Activos"
        ordering = ['-fecha_adquisicion']


class Proveedor(models.Model):
    nombre = models.CharField(max_length=200)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    direccion = models.TextField(blank=True, null=True)
    sitio_web = models.URLField(blank=True, null=True)
    notas = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Proveedor"
        verbose_name_plural = "Proveedores"


class Hardware(models.Model):
    activo = models.OneToOneField(
        Activo, on_delete=models.CASCADE, primary_key=True)
    marca = models.CharField(max_length=100)
    modelo = models.CharField(max_length=100)
    numero_serie = models.CharField(max_length=100, unique=True)
    especificaciones = models.TextField(blank=True, null=True)
    fecha_garantia = models.DateField(blank=True, null=True)
    proveedor = models.ForeignKey(
        Proveedor, on_delete=models.SET_NULL, null=True)
    periodicidad_mantenimiento = models.IntegerField(
        help_text="Periodicidad en días", default=180)

    def __str__(self):
        return f"{self.activo.nombre} - {self.marca} {self.modelo}"

    class Meta:
        verbose_name = "Hardware"
        verbose_name_plural = "Hardware"


class Software(models.Model):
    TIPO_LICENCIA_CHOICES = [
        ('perpetua', 'Perpetua'),
        ('temporal', 'Temporal'),
        ('open_source', 'Open Source'),
        ('freeware', 'Freeware'),
    ]

    activo = models.OneToOneField(
        Activo, on_delete=models.CASCADE, primary_key=True)
    version = models.CharField(max_length=50)
    tipo_licencia = models.CharField(
        max_length=20, choices=TIPO_LICENCIA_CHOICES)
    clave_activacion = models.CharField(max_length=200, blank=True, null=True)
    fecha_vencimiento = models.DateField(blank=True, null=True)
    numero_licencias = models.IntegerField(default=1)
    proveedor = models.ForeignKey(
        Proveedor, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"{self.activo.nombre} - v{self.version}"

    class Meta:
        verbose_name = "Software"
        verbose_name_plural = "Software"


class Mantenimiento(models.Model):
    TIPO_CHOICES = [
        ('preventivo', 'Preventivo'),
        ('correctivo', 'Correctivo'),
    ]
    ESTADO_CHOICES = [
        ('programado', 'Programado'),
        ('en_proceso', 'En Proceso'),
        ('completado', 'Completado'),
        ('cancelado', 'Cancelado'),
    ]

    activo = models.ForeignKey(
        Activo, on_delete=models.CASCADE, related_name='mantenimientos')
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    fecha_programada = models.DateField()
    fecha_realizacion = models.DateField(blank=True, null=True)
    responsable = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name='mantenimientos_asignados')
    descripcion = models.TextField()
    costo = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True)
    estado = models.CharField(
        max_length=20, choices=ESTADO_CHOICES, default='programado')
    observaciones = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Mantenimiento {self.get_tipo_display()} de {self.activo.nombre} - {self.fecha_programada}"

    class Meta:
        verbose_name = "Mantenimiento"
        verbose_name_plural = "Mantenimientos"
        ordering = ['-fecha_programada']


class Proceso(models.Model):
    TIPO_CHOICES = [
        ('academico', 'Académico'),
        ('administrativo', 'Administrativo'),
    ]

    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True, null=True)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    departamento = models.ForeignKey(
        Departamento, on_delete=models.CASCADE, related_name='procesos')
    responsable = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name='procesos_a_cargo')
    activos = models.ManyToManyField(Activo, through='ActivoProceso')

    def __str__(self):
        return f"{self.nombre} ({self.get_tipo_display()})"

    class Meta:
        verbose_name = "Proceso"
        verbose_name_plural = "Procesos"


class ActivoProceso(models.Model):
    NIVEL_IMPORTANCIA_CHOICES = [
        (1, 'Baja'),
        (2, 'Media'),
        (3, 'Alta'),
        (4, 'Crítica'),
    ]

    activo = models.ForeignKey(Activo, on_delete=models.CASCADE)
    proceso = models.ForeignKey(Proceso, on_delete=models.CASCADE)
    fecha_asignacion = models.DateField(auto_now_add=True)
    nivel_importancia = models.IntegerField(
        choices=NIVEL_IMPORTANCIA_CHOICES, default=2)
    observaciones = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.activo.nombre} - {self.proceso.nombre}"

    class Meta:
        verbose_name = "Activo en Proceso"
        verbose_name_plural = "Activos en Procesos"
        unique_together = ['activo', 'proceso']
