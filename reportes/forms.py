# reportes/forms.py
from django import forms
from django.contrib.auth.models import User
from usuarios.models import Departamento
from inventario.models import Activo
from .models import Reporte, ConfiguracionDashboard


class ReporteForm(forms.ModelForm):
    class Meta:
        model = Reporte
        fields = ['nombre', 'tipo', 'descripcion', 'formato']
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 3}),
        }


class InventarioReportForm(forms.Form):
    tipo = forms.ChoiceField(
        choices=[('', 'Todos'), ('hardware', 'Hardware'),
                 ('software', 'Software')],
        required=False,
        label='Tipo de Activo'
    )
    departamento = forms.ModelChoiceField(
        queryset=Departamento.objects.all(),
        required=False,
        label='Departamento',
        empty_label='Todos'
    )
    estado = forms.ChoiceField(
        choices=[
            ('', 'Todos'),
            ('activo', 'Activo'),
            ('en_mantenimiento', 'En Mantenimiento'),
            ('obsoleto', 'Obsoleto'),
            ('baja', 'De Baja')
        ],
        required=False,
        label='Estado'
    )
    fecha_inicio = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=False,
        label='Fecha de adquisición desde'
    )
    fecha_fin = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=False,
        label='Fecha de adquisición hasta'
    )
    formato = forms.ChoiceField(
        choices=[
            ('pdf', 'PDF'),
            ('excel', 'Excel')
        ],
        initial='pdf',
        label='Formato'
    )


class MantenimientoReportForm(forms.Form):
    tipo = forms.ChoiceField(
        choices=[
            ('', 'Todos'),
            ('preventivo', 'Preventivo'),
            ('correctivo', 'Correctivo')
        ],
        required=False,
        label='Tipo de Mantenimiento'
    )
    estado = forms.ChoiceField(
        choices=[
            ('', 'Todos'),
            ('programado', 'Programado'),
            ('en_proceso', 'En Proceso'),
            ('completado', 'Completado'),
            ('cancelado', 'Cancelado')
        ],
        required=False,
        label='Estado'
    )
    fecha_inicio = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=False,
        label='Fecha programada desde'
    )
    fecha_fin = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=False,
        label='Fecha programada hasta'
    )
    responsable = forms.ModelChoiceField(
        queryset=User.objects.all(),
        required=False,
        label='Responsable',
        empty_label='Todos'
    )
    formato = forms.ChoiceField(
        choices=[
            ('pdf', 'PDF'),
            ('excel', 'Excel')
        ],
        initial='pdf',
        label='Formato'
    )


class TransformacionDigitalReportForm(forms.Form):
    departamento = forms.ModelChoiceField(
        queryset=Departamento.objects.all(),
        required=False,
        label='Departamento',
        empty_label='Todos'
    )
    fecha_inicio = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=False,
        label='Fecha desde'
    )
    fecha_fin = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=False,
        label='Fecha hasta'
    )
    formato = forms.ChoiceField(
        choices=[
            ('pdf', 'PDF'),
            ('excel', 'Excel')
        ],
        initial='pdf',
        label='Formato'
    )


class DashboardConfigForm(forms.ModelForm):
    class Meta:
        model = ConfiguracionDashboard
        fields = ['widgets', 'layout']
