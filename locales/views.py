# locales/views.py - Vistas de actualización corregidas
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Local, Equipamiento
from .forms import LocalForm, EquipamientoForm, EquipamientoUpdateForm
from inventario.models import Hardware
from usuarios.models import Departamento, LogActividad


@login_required
def local_update(request, pk):
    """Actualizar local con formulario apropiado"""
    local = get_object_or_404(Local, pk=pk)

    if request.method == 'POST':
        form = LocalForm(request.POST, request.FILES, instance=local)
        if form.is_valid():
            try:
                local = form.save()

                # Registrar actividad
                LogActividad.objects.create(
                    usuario=request.user,
                    accion=f"Actualización de local: {local.nombre}",
                    detalles=f"Local tipo {local.get_tipo_display()}"
                )

                messages.success(request, 'Local actualizado correctamente.')
                return redirect('local_detail', pk=local.id)
            except Exception as e:
                print(f"Error al actualizar local: {str(e)}")
                messages.error(request, f'Error al actualizar local: {str(e)}')
        else:
            # Mostrar errores específicos del formulario
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'Error en {field}: {error}')
    else:
        # Crear formulario con la instancia - se auto-llenan los campos
        form = LocalForm(instance=local)

    # AGREGAR DEPARTAMENTOS AL CONTEXTO
    departamentos = Departamento.objects.all()

    return render(request, 'locales/local_form.html', {
        'form': form,
        'local': local,
        'is_new': False,
        'departamentos': departamentos
    })


@login_required
def local_create(request):
    """Crear local con formulario apropiado"""
    if request.method == 'POST':
        form = LocalForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                local = form.save()

                # Registrar actividad
                LogActividad.objects.create(
                    usuario=request.user,
                    accion=f"Creación de local: {local.nombre}",
                    detalles=f"Local tipo {local.get_tipo_display()}"
                )

                messages.success(request, 'Local registrado correctamente.')
                return redirect('local_detail', pk=local.id)
            except Exception as e:
                print(f"Error al crear local: {str(e)}")
                messages.error(request, f'Error al crear local: {str(e)}')
        else:
            # Mostrar errores específicos del formulario
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'Error en {field}: {error}')
    else:
        form = LocalForm()

    # AGREGAR DEPARTAMENTOS AL CONTEXTO
    departamentos = Departamento.objects.all()

    return render(request, 'locales/local_form.html', {
        'form': form,
        'is_new': True,
        'departamentos': departamentos
    })


@login_required
def equipamiento_update(request, pk):
    """Actualizar equipamiento con formulario apropiado"""
    equipamiento = get_object_or_404(Equipamiento, pk=pk)

    if request.method == 'POST':
        # Usar formulario de actualización (solo estado y notas)
        form = EquipamientoUpdateForm(request.POST, instance=equipamiento)
        if form.is_valid():
            try:
                equipamiento = form.save()

                # Registrar actividad
                LogActividad.objects.create(
                    usuario=request.user,
                    accion=f"Actualización de equipamiento: {equipamiento.hardware.activo.nombre} en {equipamiento.local.nombre}",
                    detalles=f"Estado: {equipamiento.get_estado_display()}"
                )

                messages.success(
                    request, 'Equipamiento actualizado correctamente.')
                return redirect('equipamiento_detail', pk=equipamiento.id)
            except Exception as e:
                print(f"Error al actualizar equipamiento: {str(e)}")
                messages.error(
                    request, f'Error al actualizar equipamiento: {str(e)}')
        else:
            # Mostrar errores específicos del formulario
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'Error en {field}: {error}')
    else:
        # Crear formulario con la instancia - se auto-llenan los campos
        form = EquipamientoUpdateForm(instance=equipamiento)

    return render(request, 'locales/equipamiento_form.html', {
        'form': form,
        'equipamiento': equipamiento,
        'is_new': False
    })


@login_required
def equipamiento_create(request):
    """Asignar hardware a local - crear nueva asignación"""
    if request.method == 'POST':
        form = EquipamientoForm(request.POST)
        if form.is_valid():
            try:
                equipamiento = form.save()

                # Registrar actividad
                LogActividad.objects.create(
                    usuario=request.user,
                    accion=f"Asignación de hardware a local: {equipamiento.hardware.activo.nombre} en {equipamiento.local.nombre}",
                    detalles=f"Estado: {equipamiento.get_estado_display()}"
                )

                messages.success(
                    request, 'Equipamiento asignado correctamente.')
                return redirect('equipamiento_detail', pk=equipamiento.id)
            except Exception as e:
                print(f"Error al asignar equipamiento: {str(e)}")
                messages.error(
                    request, f'Error al asignar equipamiento: {str(e)}')
        else:
            # Mostrar errores específicos del formulario
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'Error en {field}: {error}')
    else:
        form = EquipamientoForm()

    return render(request, 'locales/equipamiento_form.html', {
        'form': form,
        'is_new': True
    })


@login_required
def index(request):
    """Vista principal del módulo de locales"""
    return render(request, 'locales/index.html')


@login_required
def local_list(request):
    """Lista de locales"""
    locales = Local.objects.all().select_related('departamento')

    # Filtros
    search = request.GET.get('search', '')
    tipo = request.GET.get('tipo', '')
    departamento = request.GET.get('departamento', '')

    if search:
        locales = locales.filter(nombre__icontains=search) | locales.filter(
            ubicacion__icontains=search)

    if tipo:
        locales = locales.filter(tipo=tipo)

    if departamento:
        locales = locales.filter(departamento_id=departamento)

    return render(request, 'locales/local_list.html', {
        'locales': locales,
        'search': search,
        'tipo': tipo,
        'departamento': departamento
    })


@login_required
def local_detail(request, pk):
    """Detalle de local"""
    local = get_object_or_404(Local, pk=pk)
    equipamiento = Equipamiento.objects.filter(
        local=local).select_related('hardware', 'hardware__activo')

    # Registrar actividad
    LogActividad.objects.create(
        usuario=request.user,
        accion=f"Consulta de local: {local.nombre}",
        detalles=f"Local tipo {local.get_tipo_display()}"
    )

    return render(request, 'locales/local_detail.html', {
        'local': local,
        'equipamiento': equipamiento
    })


@login_required
def local_delete(request, pk):
    """Eliminar local"""
    local = get_object_or_404(Local, pk=pk)

    if request.method == 'POST':
        local_nombre = local.nombre
        local_id = local.id

        # Eliminar local
        local.delete()

        # Registrar actividad
        LogActividad.objects.create(
            usuario=request.user,
            accion=f"Eliminación de local: {local_nombre}",
            detalles=f"ID de local: {local_id}"
        )

        messages.success(request, 'Local eliminado correctamente.')
        return redirect('local_list')

    return render(request, 'locales/local_confirm_delete.html', {'local': local})


@login_required
def equipamiento_list(request):
    """Lista de equipamiento"""
    equipamiento = Equipamiento.objects.all().select_related(
        'local', 'hardware', 'hardware__activo')

    # Filtros
    search = request.GET.get('search', '')
    local = request.GET.get('local', '')
    estado = request.GET.get('estado', '')

    if search:
        equipamiento = equipamiento.filter(
            hardware__activo__nombre__icontains=search
        ) | equipamiento.filter(
            local__nombre__icontains=search
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
def equipamiento_detail(request, pk):
    """Detalle de equipamiento"""
    equipamiento = get_object_or_404(Equipamiento, pk=pk)

    # Registrar actividad
    LogActividad.objects.create(
        usuario=request.user,
        accion=f"Consulta de equipamiento: {equipamiento.hardware.activo.nombre} en {equipamiento.local.nombre}",
        detalles=f"Estado: {equipamiento.get_estado_display()}"
    )

    return render(request, 'locales/equipamiento_detail.html', {'equipamiento': equipamiento})


@login_required
def equipamiento_delete(request, pk):
    """Eliminar equipamiento (des-asignar hardware de local)"""
    equipamiento = get_object_or_404(Equipamiento, pk=pk)

    if request.method == 'POST':
        hardware_nombre = equipamiento.hardware.activo.nombre
        local_nombre = equipamiento.local.nombre

        # Eliminar equipamiento
        equipamiento.delete()

        # Registrar actividad
        LogActividad.objects.create(
            usuario=request.user,
            accion=f"Des-asignación de hardware de local: {hardware_nombre} de {local_nombre}",
            detalles=f"Hardware liberado para asignación"
        )

        messages.success(request, 'Equipamiento eliminado correctamente.')
        return redirect('equipamiento_list')

    return render(request, 'locales/equipamiento_confirm_delete.html', {'equipamiento': equipamiento})
