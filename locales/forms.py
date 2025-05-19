# locales/forms.py
from django import forms
from .models import Local, EquipamientoLocal
from usuarios.models import Departamento
from inventario.models import Hardware


class LocalForm(forms.ModelForm):
    class Meta:
        model = Local
        fields = ['nombre', 'tipo', 'capacidad', 'ubicacion',
                  'descripcion', 'departamento', 'estado', 'imagen', 'notas']
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 3}),
            'notas': forms.Textarea(attrs={'rows': 3}),
            'imagen': forms.FileInput(),
        }


class EquipamientoLocalForm(forms.ModelForm):
    class Meta:
        model = EquipamientoLocal
        fields = ['local', 'hardware', 'estado', 'notas']
        widgets = {
            'notas': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar hardware que no esté asignado a ningún local o que esté asignado al local actual
        if 'instance' in kwargs and kwargs['instance']:
            current_local = kwargs['instance'].local
            current_hardware = kwargs['instance'].hardware
            self.fields['hardware'].queryset = Hardware.objects.filter(
                activo__estado='activo'
            ).exclude(
                asignaciones__local__isnull=False
            ).exclude(
                asignaciones__hardware=current_hardware,
                asignaciones__local=current_local
            )
        else:
            self.fields['hardware'].queryset = Hardware.objects.filter(
                activo__estado='activo'
            ).exclude(
                asignaciones__local__isnull=False
            )
