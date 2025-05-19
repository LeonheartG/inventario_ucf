# usuarios/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import PerfilUsuario, Departamento


class RegistroForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True, label='Nombre')
    last_name = forms.CharField(
        max_length=30, required=True, label='Apellidos')
    email = forms.EmailField(
        max_length=254, required=True, label='Correo electrónico')
    departamento = forms.ModelChoiceField(
        queryset=Departamento.objects.all(), required=True, label='Departamento')
    cargo = forms.CharField(max_length=100, required=False, label='Cargo')
    telefono = forms.CharField(max_length=20, required=False, label='Teléfono')

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name',
                  'email', 'password1', 'password2')


class PerfilForm(forms.ModelForm):
    class Meta:
        model = PerfilUsuario
        fields = ('departamento', 'telefono', 'cargo', 'foto')
        widgets = {
            'foto': forms.FileInput(attrs={'class': 'form-control'}),
        }
