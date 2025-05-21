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
                if not departamento:
                    departamento = Departamento.objects.create(
                        nombre="General")

                rol, created = Rol.objects.get_or_create(
                    nombre="Usuario Regular",
                    defaults={'descripcion': 'Usuario con permisos básicos'}
                )

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

            rol, created = Rol.objects.get_or_create(
                nombre="Usuario Regular",
                defaults={'descripcion': 'Usuario con permisos básicos'}
            )

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
    # Asegurarse de que el usuario tiene un perfil
    try:
        perfil = request.user.perfil
    except PerfilUsuario.DoesNotExist:
        # Crear perfil si no existe
        departamento = Departamento.objects.first()
        if not departamento:
            departamento = Departamento.objects.create(nombre="General")

        rol, created = Rol.objects.get_or_create(
            nombre="Usuario Regular",
            defaults={'descripcion': 'Usuario con permisos básicos'}
        )

        perfil = PerfilUsuario.objects.create(
            usuario=request.user,
            departamento=departamento,
            rol=rol
        )

    if request.method == 'POST':
        form = PerfilForm(request.POST, request.FILES, instance=perfil)
        if form.is_valid():
            form.save()
            messages.success(
                request, 'Tu perfil ha sido actualizado correctamente.')
            return redirect('perfil')
    else:
        form = PerfilForm(instance=perfil)

    return render(request, 'usuarios/profile.html', {'form': form})


@login_required
def dashboard_view(request):
    """Vista del dashboard principal"""
    # Importación de modelos necesarios
    from inventario.models import Activo, Hardware, Software, Mantenimiento
    from django.db.models import Count, Sum, Q
    from django.utils import timezone
    from datetime import timedelta

    # Fechas para filtros
    hoy = timezone.now().date()
    mes_pasado = hoy - timedelta(days=30)

    # Activos
    hardware_ids = Hardware.objects.values_list('activo_id', flat=True)
    software_ids = Software.objects.values_list('activo_id', flat=True)
    total_activos = Activo.objects.filter(
        id__in=list(hardware_ids) + list(software_ids)
    ).exclude(estado='baja').count()

    total_hardware = Hardware.objects.select_related('activo').filter(
        activo__estado__in=['activo', 'en_mantenimiento', 'obsoleto']
    ).count()

    total_software = Software.objects.select_related('activo').filter(
        activo__estado__in=['activo', 'en_mantenimiento', 'obsoleto']
    ).count()

    # Mantenimientos
    mantenimientos_pendientes = Mantenimiento.objects.filter(
        Q(estado='programado') | Q(estado='en_proceso')
    ).count()

    # Equipos obsoletos
    equipos_obsoletos = Activo.objects.filter(estado='obsoleto').count()

    # Software por vencer
    software_vencer = Software.objects.filter(
        fecha_vencimiento__isnull=False,
        fecha_vencimiento__gte=hoy,
        fecha_vencimiento__lte=hoy + timedelta(days=30),
        activo__estado='activo'
    ).count()

    # Distribución por tipo
    por_tipo = [
        {'name': 'Hardware', 'value': total_hardware},
        {'name': 'Software', 'value': total_software}
    ]

    # Distribución por departamento
    por_departamento = Activo.objects.filter(
        id__in=list(hardware_ids) + list(software_ids)
    ).exclude(
        estado='baja'
    ).values(
        'departamento__nombre'
    ).annotate(
        total=Count('id')
    ).order_by('-total')[:5]

    # Obtener logs de actividad reciente
    actividades = LogActividad.objects.select_related(
        'usuario').order_by('-fecha')[:10]

    context = {
        'total_activos': total_activos,
        'total_hardware': total_hardware,
        'total_software': total_software,
        'mantenimientos_pendientes': mantenimientos_pendientes,
        'equipos_obsoletos': equipos_obsoletos,
        'software_vencer': software_vencer,
        'por_tipo': por_tipo,
        'por_departamento': por_departamento,
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
