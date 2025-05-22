# usuarios/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import PerfilUsuario, Departamento


class LoginForm(AuthenticationForm):
    """Formulario de login con mensajes de error mejorados"""
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese su nombre de usuario'
        }),
        label='Usuario'
    )

    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese su contraseña'
        }),
        label='Contraseña'
    )

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        password = cleaned_data.get('password')

        if username and password:
            # Verificar si el usuario existe
            try:
                user = User.objects.get(username=username)
                # Si el usuario existe pero la contraseña es incorrecta
                if not user.check_password(password):
                    raise ValidationError(
                        'La contraseña ingresada es incorrecta.')
                # Verificar si el usuario está activo
                if not user.is_active:
                    raise ValidationError('Esta cuenta ha sido desactivada.')
            except User.DoesNotExist:
                raise ValidationError('El usuario ingresado no existe.')

        return cleaned_data


class RegistroForm(UserCreationForm):
    """Formulario de registro con validaciones básicas"""

    first_name = forms.CharField(
        max_length=30,
        required=True,
        label='Nombre',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    last_name = forms.CharField(
        max_length=30,
        required=True,
        label='Apellidos',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    email = forms.EmailField(
        max_length=254,
        required=True,
        label='Correo electrónico',
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )

    departamento = forms.ModelChoiceField(
        queryset=Departamento.objects.all(),
        required=True,
        label='Departamento',
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    cargo = forms.CharField(
        max_length=100,
        required=False,
        label='Cargo',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    telefono = forms.CharField(
        max_length=20,
        required=False,
        label='Teléfono',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label='Nombre de usuario'
    )

    password1 = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

    password2 = forms.CharField(
        label='Confirmar contraseña',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name',
                  'email', 'password1', 'password2')

    def clean_username(self):
        """Validar que el username sea único"""
        username = self.cleaned_data.get('username')
        if username and User.objects.filter(username=username).exists():
            raise ValidationError('Este nombre de usuario ya está en uso.')
        return username

    def clean_email(self):
        """Validar que el email sea único"""
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email=email).exists():
            raise ValidationError(
                'Ya existe una cuenta con este correo electrónico.')
        return email

    def clean_password1(self):
        """Validar longitud mínima de contraseña"""
        password1 = self.cleaned_data.get('password1')
        if password1 and len(password1) < 8:
            raise ValidationError(
                'La contraseña debe tener al menos 8 caracteres.')
        return password1

    def clean_password2(self):
        """Validar que las contraseñas coincidan"""
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')

        if password1 and password2 and password1 != password2:
            raise ValidationError('Las contraseñas no coinciden.')
        return password2


class PerfilForm(forms.ModelForm):
    """Formulario para editar perfil"""

    class Meta:
        model = PerfilUsuario
        fields = ('departamento', 'telefono', 'cargo', 'foto')
        widgets = {
            'departamento': forms.Select(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'cargo': forms.TextInput(attrs={'class': 'form-control'}),
            'foto': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def clean_foto(self):
        """Validar archivo de imagen"""
        foto = self.cleaned_data.get('foto')
        if foto:
            # Validar tamaño del archivo (máximo 5MB)
            if foto.size > 5 * 1024 * 1024:
                raise ValidationError('La imagen no puede ser mayor a 5MB.')

            # Validar tipo de archivo
            valid_extensions = ['.jpg', '.jpeg', '.png', '.gif']
            if not any(foto.name.lower().endswith(ext) for ext in valid_extensions):
                raise ValidationError(
                    'Solo se permiten imágenes en formato JPG, PNG o GIF.')

        return foto


class CambiarPasswordForm(forms.Form):
    """Formulario para cambiar contraseña"""

    password_actual = forms.CharField(
        label='Contraseña actual',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

    password_nueva = forms.CharField(
        label='Nueva contraseña',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

    password_confirmacion = forms.CharField(
        label='Confirmar nueva contraseña',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_password_actual(self):
        """Validar que la contraseña actual sea correcta"""
        password_actual = self.cleaned_data.get('password_actual')
        if password_actual and not self.user.check_password(password_actual):
            raise ValidationError('La contraseña actual es incorrecta.')
        return password_actual

    def clean_password_nueva(self):
        """Validar longitud de la nueva contraseña"""
        password_nueva = self.cleaned_data.get('password_nueva')
        if password_nueva and len(password_nueva) < 8:
            raise ValidationError(
                'La contraseña debe tener al menos 8 caracteres.')
        return password_nueva

    def clean_password_confirmacion(self):
        """Validar que las contraseñas coincidan"""
        password_nueva = self.cleaned_data.get('password_nueva')
        password_confirmacion = self.cleaned_data.get('password_confirmacion')

        if password_nueva and password_confirmacion and password_nueva != password_confirmacion:
            raise ValidationError('Las contraseñas no coinciden.')
        return password_confirmacion
