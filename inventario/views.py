# inventario/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from .models import Activo, Hardware, Software, Mantenimiento
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
    """Crear hardware simplificado"""
    if request.method == 'POST':
        try:
            # Crear directamente los objetos sin usar el formulario
            activo = Activo.objects.create(
                tipo='hardware',
                nombre=request.POST.get('nombre'),
                descripcion=request.POST.get('descripcion', ''),
                fecha_adquisicion=request.POST.get('fecha_adquisicion'),
                valor_adquisicion=request.POST.get('valor_adquisicion'),
                estado=request.POST.get('estado'),
                departamento_id=request.POST.get('departamento'),
                ubicacion=request.POST.get('ubicacion', ''),
                creado_por=request.user,
                actualizado_por=request.user
            )

            if 'imagen' in request.FILES:
                activo.imagen = request.FILES['imagen']
                activo.save()

            hardware = Hardware.objects.create(
                activo=activo,
                marca=request.POST.get('marca'),
                modelo=request.POST.get('modelo'),
                numero_serie=request.POST.get('numero_serie'),
                especificaciones=request.POST.get('especificaciones', ''),
                periodicidad_mantenimiento=request.POST.get(
                    'periodicidad_mantenimiento', 180)
            )

            if request.POST.get('fecha_garantia'):
                hardware.fecha_garantia = request.POST.get('fecha_garantia')

            hardware.save()

            # Registrar Actividad
            LogActividad.objects.create(
                usuario=request.user,
                accion=f"Creación de hardware: {activo.nombre}",
                detalles=f"Hardware {hardware.marca} {hardware.modelo} con número de serie {hardware.numero_serie}"
            )

            messages.success(request, 'Hardware registrado correctamente.')
            return redirect('hardware_detail', pk=activo.id)
        except Exception as e:
            messages.error(request, f'Error al crear hardware: {str(e)}')

    # Si es GET o hubo un error, mostrar el formulario
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
            try:
                hardware = form.save(user=request.user)

                # Registrar actividad
                LogActividad.objects.create(
                    usuario=request.user,
                    accion=f"Actualización de hardware: {hardware.activo.nombre}",
                    detalles=f"Hardware {hardware.marca} {hardware.modelo} con número de serie {hardware.numero_serie}"
                )

                messages.success(
                    request, 'Hardware actualizado correctamente.')
                return redirect('hardware_detail', pk=hardware.activo_id)
            except Exception as e:
                messages.error(request, f'Error al guardar: {str(e)}')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(
                        request, f'Error en el campo {field}: {error}')
    else:
        # Crear formulario con la instancia - el __init__ se encarga de cargar los datos
        form = HardwareForm(instance=hardware)

    return render(request, 'inventario/hardware_form.html', {'form': form, 'hardware': hardware, 'is_new': False})


@login_required
def hardware_delete(request, pk):
    """Eliminar hardware"""
    hardware = get_object_or_404(Hardware, activo_id=pk)

    if request.method == 'POST':
        activo_nombre = hardware.activo.nombre
        activo_id = hardware.activo_id
        activo = hardware.activo  # Obtener referencia al activo

        # Eliminar PRIMERO el hardware, LUEGO el activo
        hardware.delete()  # Elimina el hardware
        activo.delete()    # Elimina el activo explícitamente

        # Registrar actividad
        LogActividad.objects.create(
            usuario=request.user,
            accion=f"Eliminación de hardware: {activo_nombre}",
            detalles=f"ID de activo: {activo_id} - Eliminado completamente"
        )

        messages.success(
            request, f'Hardware "{activo_nombre}" eliminado completamente.')
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
    """Crear software con enfoque directo"""
    if request.method == 'POST':
        try:
            # Crear activo
            activo = Activo.objects.create(
                tipo='software',
                nombre=request.POST.get('nombre'),
                descripcion=request.POST.get('descripcion', ''),
                fecha_adquisicion=request.POST.get('fecha_adquisicion'),
                valor_adquisicion=request.POST.get('valor_adquisicion'),
                estado=request.POST.get('estado'),
                departamento_id=request.POST.get('departamento'),
                ubicacion=request.POST.get('ubicacion', ''),
                creado_por=request.user,
                actualizado_por=request.user
            )

            if 'imagen' in request.FILES:
                activo.imagen = request.FILES['imagen']
                activo.save()

            # Crear software
            software = Software.objects.create(
                activo=activo,
                version=request.POST.get('version'),
                tipo_licencia=request.POST.get('tipo_licencia'),
                clave_activacion=request.POST.get('clave_activacion', ''),
                numero_licencias=int(request.POST.get('numero_licencias', 1))
            )

            if request.POST.get('fecha_vencimiento'):
                software.fecha_vencimiento = request.POST.get(
                    'fecha_vencimiento')

            software.save()

            # Registrar actividad
            LogActividad.objects.create(
                usuario=request.user,
                accion=f"Creación de software: {activo.nombre}",
                detalles=f"Software versión {software.version} con licencia {software.get_tipo_licencia_display()}"
            )

            messages.success(request, 'Software registrado correctamente.')
            return redirect('software_detail', pk=activo.id)
        except Exception as e:
            print(f"Error al crear software: {str(e)}")
            messages.error(request, f'Error al crear software: {str(e)}')

    # Si es GET o si hubo un error en POST
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
            try:
                software = form.save(user=request.user)

                # Registrar actividad
                LogActividad.objects.create(
                    usuario=request.user,
                    accion=f"Actualización de software: {software.activo.nombre}",
                    detalles=f"Software versión {software.version} con licencia {software.get_tipo_licencia_display()}"
                )

                messages.success(
                    request, 'Software actualizado correctamente.')
                return redirect('software_detail', pk=software.activo_id)
            except Exception as e:
                print(f"Error al actualizar software: {str(e)}")
                messages.error(
                    request, f'Error al actualizar software: {str(e)}')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(
                        request, f'Error en el campo {field}: {error}')
    else:
        # Crear formulario con la instancia - el __init__ se encarga de cargar los datos
        form = SoftwareForm(instance=software)

    return render(request, 'inventario/software_form.html', {'form': form, 'software': software, 'is_new': False})


@login_required
def software_delete(request, pk):
    """Eliminar software"""
    software = get_object_or_404(Software, activo_id=pk)

    if request.method == 'POST':
        activo_nombre = software.activo.nombre
        activo_id = software.activo_id
        activo = software.activo  # Obtener referencia al activo

        # Eliminar PRIMERO el software, LUEGO el activo
        software.delete()  # Elimina el software
        activo.delete()    # Elimina el activo explícitamente

        # Registrar actividad
        LogActividad.objects.create(
            usuario=request.user,
            accion=f"Eliminación de software: {activo_nombre}",
            detalles=f"ID de activo: {activo_id} - Eliminado completamente"
        )

        messages.success(
            request, f'Software "{activo_nombre}" eliminado completamente.')
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
    """Crear mantenimiento con enfoque directo"""
    if request.method == 'POST':
        try:
            # Obtener activo
            activo_id = request.POST.get('activo')
            if not activo_id:
                messages.error(request, 'Debe seleccionar un activo.')
                activos = Activo.objects.all()
                return render(request, 'inventario/mantenimiento_form.html', {'activos': activos, 'is_new': True})

            # Crear mantenimiento
            mantenimiento = Mantenimiento(
                activo_id=activo_id,
                tipo=request.POST.get('tipo'),
                fecha_programada=request.POST.get('fecha_programada'),
                responsable=request.user,
                descripcion=request.POST.get('descripcion', ''),
                estado=request.POST.get('estado', 'programado'),
                observaciones=request.POST.get('observaciones', '')
            )

            # Campos opcionales
            if request.POST.get('fecha_realizacion'):
                mantenimiento.fecha_realizacion = request.POST.get(
                    'fecha_realizacion')

            if request.POST.get('costo'):
                mantenimiento.costo = request.POST.get('costo')

            mantenimiento.save()

            # Registrar actividad
            activo_nombre = Activo.objects.get(id=activo_id).nombre
            LogActividad.objects.create(
                usuario=request.user,
                accion=f"Creación de mantenimiento para: {activo_nombre}",
                detalles=f"Mantenimiento {mantenimiento.get_tipo_display()}, programado para {mantenimiento.fecha_programada}"
            )

            messages.success(
                request, 'Mantenimiento registrado correctamente.')
            return redirect('mantenimiento_detail', pk=mantenimiento.id)
        except Exception as e:
            print(f"Error al crear mantenimiento: {str(e)}")
            messages.error(request, f'Error al crear mantenimiento: {str(e)}')

    # Si es GET o si hubo un error en POST
    activos = Activo.objects.all()
    usuarios = User.objects.all()

    return render(request, 'inventario/mantenimiento_form.html', {
        'activos': activos,
        'usuarios': usuarios,
        'is_new': True
    })


@login_required
def mantenimiento_detail(request, pk):
    """Detalle de mantenimiento"""
    mantenimiento = get_object_or_404(Mantenimiento, pk=pk)

    # Registrar actividad
    LogActividad.objects.create(
        usuario=request.user,
        accion=f"Consulta de mantenimiento de: {mantenimiento.activo.nombre}",
        detalles=f"Mantenimiento {mantenimiento.get_tipo_display()}, programado para {mantenimiento.fecha_programada}"
    )

    return render(request, 'inventario/mantenimiento_detail.html', {'mantenimiento': mantenimiento})


@login_required
def mantenimiento_update(request, pk):
    """Actualizar mantenimiento con enfoque directo"""
    mantenimiento = get_object_or_404(Mantenimiento, pk=pk)

    if request.method == 'POST':
        try:
            # Actualizar mantenimiento
            mantenimiento.tipo = request.POST.get('tipo')
            mantenimiento.fecha_programada = request.POST.get(
                'fecha_programada')

            if request.POST.get('responsable'):
                mantenimiento.responsable_id = request.POST.get('responsable')

            mantenimiento.descripcion = request.POST.get('descripcion', '')
            mantenimiento.estado = request.POST.get('estado')
            mantenimiento.observaciones = request.POST.get('observaciones', '')

            # Campos opcionales
            if request.POST.get('fecha_realizacion'):
                mantenimiento.fecha_realizacion = request.POST.get(
                    'fecha_realizacion')
            else:
                mantenimiento.fecha_realizacion = None

            if request.POST.get('costo'):
                mantenimiento.costo = request.POST.get('costo')
            else:
                mantenimiento.costo = None

            mantenimiento.save()

            # Registrar actividad
            LogActividad.objects.create(
                usuario=request.user,
                accion=f"Actualización de mantenimiento para: {mantenimiento.activo.nombre}",
                detalles=f"Mantenimiento {mantenimiento.get_tipo_display()}, programado para {mantenimiento.fecha_programada}"
            )

            messages.success(
                request, 'Mantenimiento actualizado correctamente.')
            return redirect('mantenimiento_detail', pk=mantenimiento.id)
        except Exception as e:
            print(f"Error al actualizar mantenimiento: {str(e)}")
            messages.error(
                request, f'Error al actualizar mantenimiento: {str(e)}')

    # Si es GET o si hubo un error en POST
    activos = Activo.objects.all()
    usuarios = User.objects.all()

    return render(request, 'inventario/mantenimiento_form.html', {
        'mantenimiento': mantenimiento,
        'activos': activos,
        'usuarios': usuarios,
        'is_new': False
    })


@login_required
def mantenimiento_delete(request, pk):
    """Eliminar mantenimiento"""
    mantenimiento = get_object_or_404(Mantenimiento, pk=pk)

    if request.method == 'POST':
        activo_nombre = mantenimiento.activo.nombre
        mantenimiento_tipo = mantenimiento.get_tipo_display()
        mantenimiento_id = mantenimiento.id

        # Eliminar mantenimiento
        mantenimiento.delete()

        # Registrar actividad
        LogActividad.objects.create(
            usuario=request.user,
            accion=f"Eliminación de mantenimiento para: {activo_nombre}",
            detalles=f"ID de mantenimiento: {mantenimiento_id}, tipo: {mantenimiento_tipo}"
        )

        messages.success(request, 'Mantenimiento eliminado correctamente.')
        return redirect('mantenimiento_list')

    return render(request, 'inventario/mantenimiento_confirm_delete.html', {'mantenimiento': mantenimiento})
