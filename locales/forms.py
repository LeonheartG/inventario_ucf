# locales/forms.py
from django import forms
from .models import Local, Equipamiento
from usuarios.models import Departamento
from inventario.models import Hardware


class LocalForm(forms.ModelForm):
    class Meta:
        model = Local
        fields = ['nombre', 'tipo', 'capacidad', 'ubicacion',
                  'descripcion', 'departamento', 'estado', 'imagen', 'notas']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo': forms.Select(attrs={'class': 'form-control'}),
            'capacidad': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'ubicacion': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'departamento': forms.Select(attrs={'class': 'form-control'}),
            'estado': forms.Select(attrs={'class': 'form-control'}),
            'imagen': forms.FileInput(attrs={'class': 'form-control'}),
            'notas': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        labels = {
            'nombre': 'Nombre',
            'tipo': 'Tipo de Local',
            'capacidad': 'Capacidad',
            'ubicacion': 'Ubicación',
            'descripcion': 'Descripción',
            'departamento': 'Departamento',
            'estado': 'Estado',
            'imagen': 'Imagen',
            'notas': 'Notas',
        }


class EquipamientoForm(forms.ModelForm):
    """Formulario para CREAR nueva asignación de equipamiento"""
    class Meta:
        model = Equipamiento
        fields = ['local', 'hardware', 'estado', 'notas']
        widgets = {
            'local': forms.Select(attrs={'class': 'form-control'}),
            'hardware': forms.Select(attrs={'class': 'form-control'}),
            'estado': forms.Select(attrs={'class': 'form-control'}),
            'notas': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        labels = {
            'local': 'Local',
            'hardware': 'Hardware',
            'estado': 'Estado',
            'notas': 'Notas',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Solo mostrar hardware disponible (no asignado)
        self.fields['hardware'].queryset = Hardware.objects.filter(
            activo__estado='activo'
        ).exclude(
            asignaciones__isnull=False
        ).select_related('activo')


class EquipamientoUpdateForm(forms.ModelForm):
    """Formulario para EDITAR asignación existente - permite cambiar local, estado y notas"""
    class Meta:
        model = Equipamiento
        # ← INCLUYE local pero NO hardware
        fields = ['local', 'estado', 'notas']
        widgets = {
            'local': forms.Select(attrs={'class': 'form-control'}),
            'estado': forms.Select(attrs={'class': 'form-control'}),
            'notas': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        labels = {
            'local': 'Local de Destino',
            'estado': 'Estado del Equipamiento',
            'notas': 'Notas',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Agregar texto de ayuda
        self.fields['local'].help_text = 'Seleccione el local donde se ubicará este equipamiento'
