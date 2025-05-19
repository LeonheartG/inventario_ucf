# Al principio del archivo usuarios/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import PerfilUsuario, Departamento, Rol, LogActividad
from .forms import RegistroForm, PerfilForm


def index(request):
    """Vista principal de la aplicación"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'usuarios/index.html')


def login_view(request):
    """Vista para iniciar sesión"""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)

            # Actualizar último acceso
            try:
                perfil = user.perfil
                perfil.ultimo_acceso = timezone.now()
                perfil.save()
            except PerfilUsuario.DoesNotExist:
                # Si el perfil no existe, crearlo
                departamento = Departamento.objects.first()
                rol = Rol.objects.get(nombre="Usuario Regular")
                PerfilUsuario.objects.create(
                    usuario=user,
                    departamento=departamento,
                    rol=rol,
                    ultimo_acceso=timezone.now()
                )

            # Registrar actividad
            LogActividad.objects.create(
                usuario=user,
                accion="Inicio de sesión",
                ip=get_client_ip(request)
            )

            messages.success(request, f'Bienvenido, {username}!')
            return redirect('dashboard')
        else:
            messages.error(
                request, 'Credenciales inválidas. Por favor, intente nuevamente.')
    return render(request, 'usuarios/login.html')


def logout_view(request):
    """Vista para cerrar sesión"""
    if request.user.is_authenticated:
        # Registrar actividad
        LogActividad.objects.create(
            usuario=request.user,
            accion="Cierre de sesión",
            ip=get_client_ip(request)
        )

    logout(request)
    messages.info(request, 'Has cerrado sesión correctamente.')
    return redirect('login')


def register_view(request):
    """Vista para registro de usuarios"""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            user = form.save()

            # Crear perfil de usuario
            departamento_id = form.cleaned_data.get('departamento')
            departamento = Departamento.objects.get(id=departamento_id)
            rol = Rol.objects.get(nombre="Usuario Regular")

            PerfilUsuario.objects.create(
                usuario=user,
                departamento=departamento,
                rol=rol,
                cargo=form.cleaned_data.get('cargo'),
                telefono=form.cleaned_data.get('telefono')
            )

            # Registrar actividad
            LogActividad.objects.create(
                usuario=user,
                accion="Registro de usuario",
                ip=get_client_ip(request)
            )

            username = form.cleaned_data.get('username')
            messages.success(
                request, f'Cuenta creada para {username}! Ya puedes iniciar sesión.')
            return redirect('login')
    else:
        form = RegistroForm()
    return render(request, 'usuarios/register.html', {'form': form})


@login_required
def profile_view(request):
    """Vista para el perfil de usuario"""
    if request.method == 'POST':
        form = PerfilForm(request.POST, request.FILES,
                          instance=request.user.perfil)
        if form.is_valid():
            form.save()
            messages.success(
                request, 'Tu perfil ha sido actualizado correctamente.')
            return redirect('perfil')
    else:
        form = PerfilForm(instance=request.user.perfil)

    return render(request, 'usuarios/profile.html', {'form': form})


@login_required
def dashboard_view(request):
    """Vista del dashboard principal"""
    # Datos para el dashboard
    from inventario.models import Activo, Hardware, Software, Mantenimiento

    # Contadores
    total_activos = Activo.objects.count()
    total_hardware = Hardware.objects.count()
    total_software = Software.objects.count()
    mantenimientos_pendientes = Mantenimiento.objects.filter(
        estado='programado').count()

    # Obtener actividades recientes
    actividades = LogActividad.objects.all().order_by('-fecha')[:10]

    context = {
        'total_activos': total_activos,
        'total_hardware': total_hardware,
        'total_software': total_software,
        'mantenimientos_pendientes': mantenimientos_pendientes,
        'actividades': actividades,
    }

    return render(request, 'usuarios/dashboard.html', context)


def get_client_ip(request):
    """Obtener IP del cliente"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
