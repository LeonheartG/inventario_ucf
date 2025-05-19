from django.db import models
from django.contrib.auth.models import User
from usuarios.models import Departamento


class Cuestionario(models.Model):
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField()
    creado_por = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name='cuestionarios_creados')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.titulo

    class Meta:
        verbose_name = "Cuestionario"
        verbose_name_plural = "Cuestionarios"


class Pregunta(models.Model):
    TIPO_CHOICES = [
        ('escala', 'Escala (1-5)'),
        ('si_no', 'Sí/No'),
        ('texto', 'Texto libre'),
    ]

    cuestionario = models.ForeignKey(
        Cuestionario, on_delete=models.CASCADE, related_name='preguntas')
    texto = models.TextField()
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    categoria = models.CharField(max_length=100)
    orden = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.texto[:50]}... ({self.get_tipo_display()})"

    class Meta:
        verbose_name = "Pregunta"
        verbose_name_plural = "Preguntas"
        ordering = ['orden']


class Diagnostico(models.Model):
    fecha = models.DateTimeField(auto_now_add=True)
    departamento = models.ForeignKey(
        Departamento, on_delete=models.CASCADE, related_name='diagnosticos')
    responsable = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='diagnosticos_realizados')
    cuestionario = models.ForeignKey(
        Cuestionario, on_delete=models.CASCADE, related_name='diagnosticos')
    nivel_general = models.FloatField(null=True, blank=True)
    observaciones = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Diagnóstico de {self.departamento.nombre} - {self.fecha.strftime('%d/%m/%Y')}"

    class Meta:
        verbose_name = "Diagnóstico"
        verbose_name_plural = "Diagnósticos"
        ordering = ['-fecha']


class Respuesta(models.Model):
    diagnostico = models.ForeignKey(
        Diagnostico, on_delete=models.CASCADE, related_name='respuestas')
    pregunta = models.ForeignKey(
        Pregunta, on_delete=models.CASCADE, related_name='respuestas')
    valor_numerico = models.IntegerField(null=True, blank=True)
    valor_texto = models.TextField(null=True, blank=True)

    def __str__(self):
        if self.valor_numerico is not None:
            return f"Respuesta: {self.valor_numerico}"
        return f"Respuesta: {self.valor_texto}"

    class Meta:
        verbose_name = "Respuesta"
        verbose_name_plural = "Respuestas"
        unique_together = ['diagnostico', 'pregunta']


class IndicadorDiagnostico(models.Model):
    diagnostico = models.ForeignKey(
        Diagnostico, on_delete=models.CASCADE, related_name='indicadores')
    nombre = models.CharField(max_length=100)
    valor = models.FloatField()
    descripcion = models.TextField(blank=True, null=True)
    recomendacion = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.nombre}: {self.valor}"

    class Meta:
        verbose_name = "Indicador de Diagnóstico"
        verbose_name_plural = "Indicadores de Diagnóstico"
