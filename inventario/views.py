# Al principio del archivo inventario/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Activo, Hardware, Software, Mantenimiento, Proveedor
from .forms import HardwareForm, SoftwareForm
from usuarios.models import LogActividad


@login_required
def index(request):
    """Vista principal del módulo de inventario"""
    return render(request, 'inventario/index.html')

# Hardware views


@login_required
def hardware_list(request):
    """Lista de hardware"""
    hardware_list = Hardware.objects.all().select_related(
        'activo', 'activo__departamento')

    # Filtros
    search = request.GET.get('search', '')
    departamento = request.GET.get('departamento', '')
    estado = request.GET.get('estado', '')

    if search:
        hardware_list = hardware_list.filter(
            activo__nombre__icontains=search
        ) | hardware_list.filter(
            marca__icontains=search
        ) | hardware_list.filter(
            modelo__icontains=search
        ) | hardware_list.filter(
            numero_serie__icontains=search
        )

    if departamento:
        hardware_list = hardware_list.filter(
            activo__departamento_id=departamento)

    if estado:
        hardware_list = hardware_list.filter(activo__estado=estado)

    return render(request, 'inventario/hardware_list.html', {
        'hardware_list': hardware_list,
        'search': search,
        'departamento': departamento,
        'estado': estado
    })


@login_required
def hardware_create(request):
    """Crear hardware"""
    if request.method == 'POST':
        form = HardwareForm(request.POST, request.FILES)
        if form.is_valid():
            hardware = form.save(user=request.user)

            # Registrar actividad
            LogActividad.objects.create(
                usuario=request.user,
                accion=f"Creación de hardware: {hardware.activo.nombre}",
                detalles=f"Hardware {hardware.marca} {hardware.modelo} con número de serie {hardware.numero_serie}"
            )

            messages.success(request, 'Hardware registrado correctamente.')
            return redirect('hardware_detail', pk=hardware.activo_id)
    else:
        form = HardwareForm()

    return render(request, 'inventario/hardware_form.html', {'form': form, 'is_new': True})


@login_required
def hardware_detail(request, pk):
    """Detalle de hardware"""
    hardware = get_object_or_404(Hardware, activo_id=pk)

    # Registrar actividad
    LogActividad.objects.create(
        usuario=request.user,
        accion=f"Consulta de hardware: {hardware.activo.nombre}",
        detalles=f"Hardware {hardware.marca} {hardware.modelo} con número de serie {hardware.numero_serie}"
    )

    return render(request, 'inventario/hardware_detail.html', {'hardware': hardware})


@login_required
def hardware_update(request, pk):
    """Actualizar hardware"""
    hardware = get_object_or_404(Hardware, activo_id=pk)

    if request.method == 'POST':
        form = HardwareForm(request.POST, request.FILES, instance=hardware)
        if form.is_valid():
            hardware = form.save(user=request.user)

            # Registrar actividad
            LogActividad.objects.create(
                usuario=request.user,
                accion=f"Actualización de hardware: {hardware.activo.nombre}",
                detalles=f"Hardware {hardware.marca} {hardware.modelo} con número de serie {hardware.numero_serie}"
            )

            messages.success(request, 'Hardware actualizado correctamente.')
            return redirect('hardware_detail', pk=hardware.activo_id)
    else:
        # Inicializar el formulario con los datos del activo y hardware
        initial_data = {
            'nombre': hardware.activo.nombre,
            'descripcion': hardware.activo.descripcion,
            'fecha_adquisicion': hardware.activo.fecha_adquisicion,
            'valor_adquisicion': hardware.activo.valor_adquisicion,
            'estado': hardware.activo.estado,
            'departamento': hardware.activo.departamento,
            'ubicacion': hardware.activo.ubicacion,
            'marca': hardware.marca,
            'modelo': hardware.modelo,
            'numero_serie': hardware.numero_serie,
            'especificaciones': hardware.especificaciones,
            'fecha_garantia': hardware.fecha_garantia,
            'proveedor': hardware.proveedor,
            'periodicidad_mantenimiento': hardware.periodicidad_mantenimiento
        }
        form = HardwareForm(instance=hardware, initial=initial_data)

    return render(request, 'inventario/hardware_form.html', {'form': form, 'hardware': hardware, 'is_new': False})


@login_required
def hardware_delete(request, pk):
    """Eliminar hardware"""
    hardware = get_object_or_404(Hardware, activo_id=pk)

    if request.method == 'POST':
        activo_nombre = hardware.activo.nombre
        activo_id = hardware.activo_id

        # Eliminar el hardware y su activo asociado
        hardware.delete()  # Esto eliminará el hardware y el activo asociado en cascada

        # Registrar actividad
        LogActividad.objects.create(
            usuario=request.user,
            accion=f"Eliminación de hardware: {activo_nombre}",
            detalles=f"ID de activo: {activo_id}"
        )

        messages.success(
            request, f'Hardware "{activo_nombre}" eliminado correctamente.')
        return redirect('hardware_list')

    return render(request, 'inventario/hardware_confirm_delete.html', {'hardware': hardware})


@login_required
def software_list(request):
    """Lista de software"""
    software_list = Software.objects.all().select_related(
        'activo', 'activo__departamento')

    # Filtros
    search = request.GET.get('search', '')
    departamento = request.GET.get('departamento', '')
    estado = request.GET.get('estado', '')

    if search:
        software_list = software_list.filter(
            activo__nombre__icontains=search
        ) | software_list.filter(
            version__icontains=search
        ) | software_list.filter(
            tipo_licencia__icontains=search
        )

    if departamento:
        software_list = software_list.filter(
            activo__departamento_id=departamento)

    if estado:
        software_list = software_list.filter(activo__estado=estado)

    return render(request, 'inventario/software_list.html', {
        'software_list': software_list,
        'search': search,
        'departamento': departamento,
        'estado': estado
    })


@login_required
def software_create(request):
    """Crear software"""
    if request.method == 'POST':
        form = SoftwareForm(request.POST, request.FILES)
        if form.is_valid():
            software = form.save(user=request.user)

            # Registrar actividad
            LogActividad.objects.create(
                usuario=request.user,
                accion=f"Creación de software: {software.activo.nombre}",
                detalles=f"Software versión {software.version} con licencia {software.get_tipo_licencia_display()}"
            )

            messages.success(request, 'Software registrado correctamente.')
            return redirect('software_detail', pk=software.activo_id)
    else:
        form = SoftwareForm()

    return render(request, 'inventario/software_form.html', {'form': form, 'is_new': True})


@login_required
def software_detail(request, pk):
    """Detalle de software"""
    software = get_object_or_404(Software, activo_id=pk)

    # Registrar actividad
    LogActividad.objects.create(
        usuario=request.user,
        accion=f"Consulta de software: {software.activo.nombre}",
        detalles=f"Software versión {software.version}"
    )

    return render(request, 'inventario/software_detail.html', {'software': software})


@login_required
def software_update(request, pk):
    """Actualizar software"""
    software = get_object_or_404(Software, activo_id=pk)

    if request.method == 'POST':
        form = SoftwareForm(request.POST, request.FILES, instance=software)
        if form.is_valid():
            software = form.save(user=request.user)

            # Registrar actividad
            LogActividad.objects.create(
                usuario=request.user,
                accion=f"Actualización de software: {software.activo.nombre}",
                detalles=f"Software versión {software.version}"
            )

            messages.success(request, 'Software actualizado correctamente.')
            return redirect('software_detail', pk=software.activo_id)
    else:
        # Inicializar el formulario con los datos del activo y software
        initial_data = {
            'nombre': software.activo.nombre,
            'descripcion': software.activo.descripcion,
            'fecha_adquisicion': software.activo.fecha_adquisicion,
            'valor_adquisicion': software.activo.valor_adquisicion,
            'estado': software.activo.estado,
            'departamento': software.activo.departamento,
            'ubicacion': software.activo.ubicacion,
            'version': software.version,
            'tipo_licencia': software.tipo_licencia,
            'clave_activacion': software.clave_activacion,
            'fecha_vencimiento': software.fecha_vencimiento,
            'numero_licencias': software.numero_licencias,
            'proveedor': software.proveedor
        }
        form = SoftwareForm(instance=software, initial=initial_data)

    return render(request, 'inventario/software_form.html', {'form': form, 'software': software, 'is_new': False})


@login_required
def software_delete(request, pk):
    """Eliminar software"""
    software = get_object_or_404(Software, activo_id=pk)

    if request.method == 'POST':
        activo_nombre = software.activo.nombre
        activo_id = software.activo_id

        # Eliminar el software y su activo asociado
        software.delete()  # Esto eliminará el software y el activo asociado en cascada

        # Registrar actividad
        LogActividad.objects.create(
            usuario=request.user,
            accion=f"Eliminación de software: {activo_nombre}",
            detalles=f"ID de activo: {activo_id}"
        )

        messages.success(
            request, f'Software "{activo_nombre}" eliminado correctamente.')
        return redirect('software_list')

    return render(request, 'inventario/software_confirm_delete.html', {'software': software})


@login_required
def mantenimiento_list(request):
    """Lista de mantenimientos"""
    mantenimientos = Mantenimiento.objects.all().select_related('activo', 'responsable')

    # Filtros
    search = request.GET.get('search', '')
    tipo = request.GET.get('tipo', '')
    estado = request.GET.get('estado', '')

    if search:
        mantenimientos = mantenimientos.filter(
            activo__nombre__icontains=search
        ) | mantenimientos.filter(
            descripcion__icontains=search
        )

    if tipo:
        mantenimientos = mantenimientos.filter(tipo=tipo)

    if estado:
        mantenimientos = mantenimientos.filter(estado=estado)

    return render(request, 'inventario/mantenimiento_list.html', {
        'mantenimientos': mantenimientos,
        'search': search,
        'tipo': tipo,
        'estado': estado
    })


@login_required
def mantenimiento_create(request):
    """Crear mantenimiento"""
    # Implementación simplificada
    return render(request, 'inventario/mantenimiento_form.html')


@login_required
def mantenimiento_detail(request, pk):
    """Detalle de mantenimiento"""
    # Implementación simplificada
    mantenimiento = get_object_or_404(Mantenimiento, pk=pk)
    return render(request, 'inventario/mantenimiento_detail.html', {'mantenimiento': mantenimiento})


@login_required
def mantenimiento_update(request, pk):
    """Actualizar mantenimiento"""
    # Implementación simplificada
    mantenimiento = get_object_or_404(Mantenimiento, pk=pk)
    return render(request, 'inventario/mantenimiento_form.html', {'mantenimiento': mantenimiento})


@login_required
def mantenimiento_delete(request, pk):
    """Eliminar mantenimiento"""
    # Implementación simplificada
    mantenimiento = get_object_or_404(Mantenimiento, pk=pk)
    return render(request, 'inventario/mantenimiento_confirm_delete.html', {'mantenimiento': mantenimiento})
