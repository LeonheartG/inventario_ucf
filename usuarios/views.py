# usuarios/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
from .models import PerfilUsuario, Departamento, Rol, LogActividad
from .forms import RegistroForm, PerfilForm, LoginForm, CambiarPasswordForm
from .decorators import puede_ver_actividad, puede_ver_reportes


def index(request):
    """Vista principal de la aplicación - redirige al login si no está autenticado"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    else:
        return redirect('login')


def login_view(request):
    """Vista para iniciar sesión"""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)

            if user is not None:
                login(request, user)

                # Actualizar último acceso
                try:
                    perfil = user.perfil
                    perfil.ultimo_acceso = timezone.now()
                    perfil.save()
                except PerfilUsuario.DoesNotExist:
                    # Crear perfil si no existe
                    departamento = Departamento.objects.first()
                    rol, created = Rol.objects.get_or_create(
                        nombre="Usuario Regular",
                        defaults={
                            'descripcion': 'Usuario con permisos básicos'}
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

                messages.success(
                    request, f'¡Bienvenido, {user.get_full_name() or username}!')
                return redirect('dashboard')
    else:
        form = LoginForm()

    return render(request, 'usuarios/login.html', {'form': form})


def logout_view(request):
    """Vista para cerrar sesión"""
    if request.user.is_authenticated:
        # Registrar actividad
        LogActividad.objects.create(
            usuario=request.user,
            accion="Cierre de sesión",
            ip=get_client_ip(request)
        )
        username = request.user.username
        logout(request)
        messages.info(
            request, f'Has cerrado sesión correctamente, {username}.')
    else:
        messages.info(request, 'Sesión cerrada.')

    return redirect('login')


def register_view(request):
    """Vista para registro de usuarios"""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Crear usuario
                    user = form.save()

                    # Obtener datos adicionales del formulario
                    departamento = form.cleaned_data.get('departamento')
                    telefono = form.cleaned_data.get('telefono')

                    # El perfil ya fue creado por el signal, ahora lo actualizamos
                    try:
                        perfil = user.perfil
                        perfil.departamento = departamento
                        perfil.telefono = telefono or ''
                        perfil.save()
                    except PerfilUsuario.DoesNotExist:
                        # Si por alguna razón no se creó el perfil, lo creamos
                        rol, created = Rol.objects.get_or_create(
                            nombre="Usuario Regular",
                            defaults={
                                'descripcion': 'Usuario con permisos básicos del sistema'}
                        )

                        PerfilUsuario.objects.create(
                            usuario=user,
                            departamento=departamento,
                            rol=rol,
                            telefono=telefono or ''
                        )

                    # Registrar actividad
                    LogActividad.objects.create(
                        usuario=user,
                        accion="Registro de usuario",
                        ip=get_client_ip(request)
                    )

                    username = form.cleaned_data.get('username')
                    messages.success(
                        request,
                        f'¡Cuenta creada exitosamente para {username}! Ya puedes iniciar sesión.'
                    )
                    return redirect('login')

            except Exception as e:
                # Mostrar el error específico para debug (solo en desarrollo)
                import traceback
                print(f"Error en registro: {str(e)}")
                print(traceback.format_exc())

                # Mostrar mensaje de error más específico
                if 'UNIQUE constraint' in str(e):
                    messages.error(
                        request, 'Ya existe un usuario con ese nombre o correo electrónico.')
                elif 'NOT NULL constraint' in str(e):
                    messages.error(
                        request, 'Faltan datos requeridos en el formulario.')
                else:
                    messages.error(
                        request, f'Error al crear la cuenta: {str(e)}')
        else:
            # Mostrar errores específicos del formulario
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'Error en {field}: {error}')
    else:
        form = RegistroForm()

    return render(request, 'usuarios/register.html', {'form': form})


@login_required
def profile_view(request):
    """Vista para el perfil de usuario"""
    try:
        perfil = request.user.perfil
    except PerfilUsuario.DoesNotExist:
        # Crear perfil si no existe
        departamento = Departamento.objects.first()
        if not departamento:
            departamento = Departamento.objects.create(
                nombre="General",
                descripcion="Departamento general para usuarios sin asignación específica"
            )

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
            try:
                form.save()

                # Registrar actividad
                LogActividad.objects.create(
                    usuario=request.user,
                    accion="Actualización de perfil",
                    ip=get_client_ip(request)
                )

                messages.success(
                    request, 'Tu perfil ha sido actualizado correctamente.')
                return redirect('perfil')
            except Exception as e:
                messages.error(
                    request, 'Error al actualizar el perfil. Por favor, intente nuevamente.')
        else:
            messages.error(
                request, 'Por favor, corrija los errores en el formulario.')
    else:
        form = PerfilForm(instance=perfil)

    # Obtener actividades recientes del usuario
    actividades = LogActividad.objects.filter(
        usuario=request.user
    ).order_by('-fecha')[:5]

    context = {
        'form': form,
        'perfil': perfil,
        'actividades': actividades
    }

    return render(request, 'usuarios/profile.html', context)


@login_required
def cambiar_password_view(request):
    """Vista para cambiar contraseña"""
    if request.method == 'POST':
        form = CambiarPasswordForm(request.user, request.POST)
        if form.is_valid():
            # Cambiar la contraseña
            request.user.set_password(form.cleaned_data['password_nueva'])
            request.user.save()

            # Mantener la sesión activa después del cambio de contraseña
            update_session_auth_hash(request, request.user)

            # Registrar actividad
            LogActividad.objects.create(
                usuario=request.user,
                accion="Cambio de contraseña",
                ip=get_client_ip(request)
            )

            messages.success(
                request, 'Tu contraseña ha sido cambiada exitosamente.')
            return redirect('perfil')
    else:
        form = CambiarPasswordForm(request.user)

    return render(request, 'usuarios/cambiar_password.html', {'form': form})


@login_required
def dashboard_view(request):
    """Vista del dashboard principal con restricciones por rol"""
    try:
        # Importación de modelos necesarios
        from inventario.models import Activo, Hardware, Software, Mantenimiento
        from django.db.models import Count, Q
        from django.utils import timezone
        from datetime import timedelta

        # Fechas para filtros
        hoy = timezone.now().date()

        # Obtener estadísticas de manera segura
        try:
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
            equipos_obsoletos = Activo.objects.filter(
                estado='obsoleto').count()

            # Software por vencer
            software_vencer = Software.objects.filter(
                fecha_vencimiento__isnull=False,
                fecha_vencimiento__gte=hoy,
                fecha_vencimiento__lte=hoy + timedelta(days=30),
                activo__estado='activo'
            ).count()

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

        except Exception:
            # Valores por defecto en caso de error
            total_activos = 0
            total_hardware = 0
            total_software = 0
            mantenimientos_pendientes = 0
            equipos_obsoletos = 0
            software_vencer = 0
            por_departamento = []

        # Verificar permisos para actividad reciente
        actividades = []
        mostrar_actividad = puede_ver_actividad(request.user)

        if mostrar_actividad:
            try:
                actividades = LogActividad.objects.select_related(
                    'usuario').order_by('-fecha')[:10]
            except Exception:
                actividades = []

        # Verificar permisos para reportes
        puede_reportes = puede_ver_reportes(request.user)

        # Obtener información del rol para mostrar en el template
        rol_usuario = "Usuario Regular"
        try:
            if hasattr(request.user, 'perfil') and request.user.perfil.rol:
                rol_usuario = request.user.perfil.rol.nombre
        except Exception:
            pass

        context = {
            'total_activos': total_activos,
            'total_hardware': total_hardware,
            'total_software': total_software,
            'mantenimientos_pendientes': mantenimientos_pendientes,
            'equipos_obsoletos': equipos_obsoletos,
            'software_vencer': software_vencer,
            'por_departamento': por_departamento,
            'actividades': actividades,
            'mostrar_actividad': mostrar_actividad,
            'puede_reportes': puede_reportes,
            'rol_usuario': rol_usuario,
        }

        return render(request, 'usuarios/dashboard.html', context)

    except Exception as e:
        messages.error(request, 'Error al cargar el dashboard.')

        # Contexto mínimo en caso de error
        context = {
            'total_activos': 0,
            'total_hardware': 0,
            'total_software': 0,
            'mantenimientos_pendientes': 0,
            'equipos_obsoletos': 0,
            'software_vencer': 0,
            'por_departamento': [],
            'actividades': [],
            'mostrar_actividad': False,
            'puede_reportes': False,
            'rol_usuario': 'Usuario Regular',
        }
        return render(request, 'usuarios/dashboard.html', context)


def get_client_ip(request):
    """Obtener IP del cliente"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip or '0.0.0.0'
