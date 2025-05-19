# locales/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Local, EquipamientoLocal
from .forms import LocalForm, EquipamientoLocalForm
from usuarios.models import LogActividad


@login_required
def index(request):
    """Vista principal del módulo de locales"""
    return render(request, 'locales/index.html')

# Local views


@login_required
def local_list(request):
    """Lista de locales"""
    locales = Local.objects.all().select_related('departamento')

    # Filtros
    search = request.GET.get('search', '')
    tipo = request.GET.get('tipo', '')
    departamento = request.GET.get('departamento', '')
    estado = request.GET.get('estado', '')

    if search:
        locales = locales.filter(nombre__icontains=search) | locales.filter(
            ubicacion__icontains=search)

    if tipo:
        locales = locales.filter(tipo=tipo)

    if departamento:
        locales = locales.filter(departamento_id=departamento)

    if estado:
        locales = locales.filter(estado=estado)

    return render(request, 'locales/local_list.html', {
        'locales': locales,
        'search': search,
        'tipo': tipo,
        'departamento': departamento,
        'estado': estado
    })


@login_required
def local_create(request):
    """Crear local"""
    if request.method == 'POST':
        form = LocalForm(request.POST, request.FILES)
        if form.is_valid():
            local = form.save()

            # Registrar actividad
            LogActividad.objects.create(
                usuario=request.user,
                accion=f"Creación de local: {local.nombre}",
                detalles=f"Local tipo {local.get_tipo_display()} en {local.ubicacion}"
            )

            messages.success(request, 'Local registrado correctamente.')
            return redirect('local_detail', pk=local.id)
    else:
        form = LocalForm()

    return render(request, 'locales/local_form.html', {'form': form, 'is_new': True})


@login_required
def local_detail(request, pk):
    """Detalle de local"""
    local = get_object_or_404(Local, pk=pk)
    equipamiento = EquipamientoLocal.objects.filter(
        local=local).select_related('hardware', 'hardware__activo')

    # Registrar actividad
    LogActividad.objects.create(
        usuario=request.user,
        accion=f"Consulta de local: {local.nombre}",
        detalles=f"Local tipo {local.get_tipo_display()} en {local.ubicacion}"
    )

    return render(request, 'locales/local_detail.html', {
        'local': local,
        'equipamiento': equipamiento
    })


@login_required
def local_update(request, pk):
    """Actualizar local"""
    local = get_object_or_404(Local, pk=pk)

    if request.method == 'POST':
        form = LocalForm(request.POST, request.FILES, instance=local)
        if form.is_valid():
            local = form.save()

            # Registrar actividad
            LogActividad.objects.create(
                usuario=request.user,
                accion=f"Actualización de local: {local.nombre}",
                detalles=f"Local tipo {local.get_tipo_display()} en {local.ubicacion}"
            )

            messages.success(request, 'Local actualizado correctamente.')
            return redirect('local_detail', pk=local.id)
    else:
        form = LocalForm(instance=local)

    return render(request, 'locales/local_form.html', {'form': form, 'local': local, 'is_new': False})


@login_required
def local_delete(request, pk):
    """Eliminar local"""
    local = get_object_or_404(Local, pk=pk)

    if request.method == 'POST':
        nombre = local.nombre

        # Eliminar el local
        local.delete()

        # Registrar actividad
        LogActividad.objects.create(
            usuario=request.user,
            accion=f"Eliminación de local: {nombre}",
            detalles=f"ID: {pk}"
        )

        messages.success(request, f'Local "{nombre}" eliminado correctamente.')
        return redirect('local_list')

    return render(request, 'locales/local_confirm_delete.html', {'local': local})

# Equipamiento views


@login_required
def equipamiento_list(request):
    """Lista de equipamientos"""
    equipamiento = EquipamientoLocal.objects.all().select_related(
        'local', 'hardware', 'hardware__activo')

    # Filtros
    search = request.GET.get('search', '')
    local = request.GET.get('local', '')
    estado = request.GET.get('estado', '')

    if search:
        equipamiento = equipamiento.filter(
            local__nombre__icontains=search
        ) | equipamiento.filter(
            hardware__activo__nombre__icontains=search
        )

    if local:
        equipamiento = equipamiento.filter(local_id=local)

    if estado:
        equipamiento = equipamiento.filter(estado=estado)

    return render(request, 'locales/equipamiento_list.html', {
        'equipamiento': equipamiento,
        'search': search,
        'local': local,
        'estado': estado
    })


@login_required
def equipamiento_create(request):
    """Crear equipamiento"""
    if request.method == 'POST':
        form = EquipamientoLocalForm(request.POST)
        if form.is_valid():
            equipamiento = form.save()

            # Registrar actividad
            LogActividad.objects.create(
                usuario=request.user,
                accion=f"Asignación de equipamiento a local",
                detalles=f"Hardware '{equipamiento.hardware.activo.nombre}' asignado a local '{equipamiento.local.nombre}'"
            )

            messages.success(request, 'Equipamiento asignado correctamente.')
            return redirect('equipamiento_detail', pk=equipamiento.id)
    else:
        form = EquipamientoLocalForm()

    return render(request, 'locales/equipamiento_form.html', {'form': form, 'is_new': True})


@login_required
def equipamiento_detail(request, pk):
    """Detalle de equipamiento"""
    equipamiento = get_object_or_404(EquipamientoLocal, pk=pk)

    # Registrar actividad
    LogActividad.objects.create(
        usuario=request.user,
        accion=f"Consulta de equipamiento",
        detalles=f"Hardware '{equipamiento.hardware.activo.nombre}' en local '{equipamiento.local.nombre}'"
    )

    return render(request, 'locales/equipamiento_detail.html', {'equipamiento': equipamiento})


@login_required
def equipamiento_update(request, pk):
    """Actualizar equipamiento"""
    equipamiento = get_object_or_404(EquipamientoLocal, pk=pk)

    if request.method == 'POST':
        form = EquipamientoLocalForm(request.POST, instance=equipamiento)
        if form.is_valid():
            equipamiento = form.save()

            # Registrar actividad
            LogActividad.objects.create(
                usuario=request.user,
                accion=f"Actualización de equipamiento",
                detalles=f"Hardware '{equipamiento.hardware.activo.nombre}' en local '{equipamiento.local.nombre}'"
            )

            messages.success(
                request, 'Equipamiento actualizado correctamente.')
            return redirect('equipamiento_detail', pk=equipamiento.id)
    else:
        form = EquipamientoLocalForm(instance=equipamiento)

    return render(request, 'locales/equipamiento_form.html', {'form': form, 'equipamiento': equipamiento, 'is_new': False})


@login_required
def equipamiento_delete(request, pk):
    """Eliminar equipamiento"""
    equipamiento = get_object_or_404(EquipamientoLocal, pk=pk)

    if request.method == 'POST':
        hardware_nombre = equipamiento.hardware.activo.nombre
        local_nombre = equipamiento.local.nombre

        # Eliminar el equipamiento
        equipamiento.delete()

        # Registrar actividad
        LogActividad.objects.create(
            usuario=request.user,
            accion=f"Eliminación de equipamiento",
            detalles=f"Hardware '{hardware_nombre}' del local '{local_nombre}'"
        )

        messages.success(request, 'Equipamiento eliminado correctamente.')
        return redirect('equipamiento_list')

    return render(request, 'locales/equipamiento_confirm_delete.html', {'equipamiento': equipamiento})
