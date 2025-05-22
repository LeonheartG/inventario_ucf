# reportes/forms.py
from django import forms
from django.contrib.auth.models import User
from usuarios.models import Departamento


class InventarioReportForm(forms.Form):
    """Formulario para filtros de reporte de inventario"""

    TIPO_CHOICES = [
        ('', 'Todos'),
        ('hardware', 'Hardware'),
        ('software', 'Software'),
    ]

    ESTADO_CHOICES = [
        ('', 'Todos'),
        ('activo', 'Activo'),
        ('en_mantenimiento', 'En Mantenimiento'),
        ('obsoleto', 'Obsoleto'),
        ('baja', 'De Baja'),
    ]

    FORMATO_CHOICES = [
        ('pdf', 'PDF'),
        ('excel', 'Excel'),
    ]

    tipo = forms.ChoiceField(
        choices=TIPO_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    departamento = forms.ModelChoiceField(
        queryset=Departamento.objects.all(),
        required=False,
        empty_label="Todos",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    estado = forms.ChoiceField(
        choices=ESTADO_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    fecha_inicio = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='Fecha de adquisición desde'
    )

    fecha_fin = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='Fecha de adquisición hasta'
    )

    formato = forms.ChoiceField(
        choices=FORMATO_CHOICES,
        initial='pdf',
        widget=forms.Select(attrs={'class': 'form-control'})
    )


class MantenimientoReportForm(forms.Form):
    """Formulario para filtros de reporte de mantenimientos"""

    TIPO_CHOICES = [
        ('', 'Todos'),
        ('preventivo', 'Preventivo'),
        ('correctivo', 'Correctivo'),
    ]

    ESTADO_CHOICES = [
        ('', 'Todos'),
        ('programado', 'Programado'),
        ('en_proceso', 'En Proceso'),
        ('completado', 'Completado'),
        ('cancelado', 'Cancelado'),
    ]

    FORMATO_CHOICES = [
        ('pdf', 'PDF'),
        ('excel', 'Excel'),
    ]

    tipo = forms.ChoiceField(
        choices=TIPO_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    estado = forms.ChoiceField(
        choices=ESTADO_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    responsable = forms.ModelChoiceField(
        queryset=User.objects.filter(is_active=True).order_by(
            'first_name', 'last_name'),
        required=False,
        empty_label="Todos",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    fecha_inicio = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='Fecha programada desde'
    )

    fecha_fin = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='Fecha programada hasta'
    )

    formato = forms.ChoiceField(
        choices=FORMATO_CHOICES,
        initial='pdf',
        widget=forms.Select(attrs={'class': 'form-control'})
    )


class TransformacionDigitalReportForm(forms.Form):
    """Formulario para filtros de reporte de transformación digital"""

    FORMATO_CHOICES = [
        ('pdf', 'PDF'),
        ('excel', 'Excel'),
    ]

    departamento = forms.ModelChoiceField(
        queryset=Departamento.objects.all(),
        required=False,
        empty_label="Todos los departamentos",
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Departamento'
    )

    fecha_inicio = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='Fecha de evaluación desde'
    )

    fecha_fin = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='Fecha de evaluación hasta'
    )

    formato = forms.ChoiceField(
        choices=FORMATO_CHOICES,
        initial='pdf',
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Formato de exportación'
    )
