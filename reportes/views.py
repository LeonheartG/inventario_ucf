# reportes/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from datetime import datetime, timedelta
import json
from django.db.models import Count, Sum, Avg, Q
from .utils import PDFExporter, ExcelExporter, export_queryset_to_pdf, export_queryset_to_excel

# Importaciones de modelos
from inventario.models import Activo, Hardware, Software, Mantenimiento
from usuarios.models import Departamento, User
from locales.models import Local, Equipamiento

# Importaciones condicionales para diagnóstico
try:
    from diagnostico.models import Diagnostico, IndicadorDiagnostico
    DIAGNOSTICO_AVAILABLE = True
except ImportError:
    DIAGNOSTICO_AVAILABLE = False

from usuarios.decorators import (
    supervisor_o_admin_requerido,
    puede_ver_reportes,
    puede_ver_actividad,
    es_admin
)

# Context processor para permisos globales


def permisos_context(request):
    """
    Context processor para agregar permisos a todos los templates
    """
    context = {}

    if request.user.is_authenticated:
        context.update({
            'puede_ver_reportes': puede_ver_reportes(request.user),
            'puede_ver_actividad': puede_ver_actividad(request.user),
            'es_admin': es_admin(request.user),
        })
    else:
        context.update({
            'puede_ver_reportes': False,
            'puede_ver_actividad': False,
            'es_admin': False,
        })

    return context


@supervisor_o_admin_requerido
def reportes_index_view(request):
    """Vista principal de reportes - Solo supervisores y admins"""
    context = {
        'section': 'reportes',
        'title': 'Centro de Reportes'
    }
    return render(request, 'reportes/index.html', context)


@supervisor_o_admin_requerido
def dashboard_view(request):
    """Dashboard de reportes - Solo supervisores y admins"""
    try:
        # Importar modelos de inventario de manera segura
        from inventario.models import Activo, Hardware, Software, Mantenimiento
        from usuarios.models import LogActividad
        from django.db.models import Count, Q, Sum, Avg
        from datetime import datetime, timedelta

        # Estadísticas generales
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

            # Mantenimientos pendientes
            mantenimientos_pendientes = Mantenimiento.objects.filter(
                Q(estado='programado') | Q(estado='en_proceso')
            ).count()

            # Nivel de transformación digital (si existe módulo diagnóstico)
            nivel_transformacion = 0
            try:
                from diagnostico.models import Diagnostico
                diagnosticos = Diagnostico.objects.filter(
                    nivel_general__isnull=False)
                if diagnosticos.exists():
                    nivel_transformacion = diagnosticos.aggregate(
                        promedio=Avg('nivel_general')
                    )['promedio'] or 0
            except ImportError:
                pass

            # Activos por departamento para gráfico
            activos_por_departamento = Activo.objects.filter(
                id__in=list(hardware_ids) + list(software_ids)
            ).exclude(estado='baja').values(
                'departamento__nombre'
            ).annotate(total=Count('id')).order_by('-total')[:10]

            # Activos por estado
            activos_por_estado = Activo.objects.filter(
                id__in=list(hardware_ids) + list(software_ids)
            ).values('estado').annotate(total=Count('id')).order_by('-total')

            # Software próximo a vencer
            hoy = timezone.now().date()
            software_por_vencer = Software.objects.filter(
                fecha_vencimiento__isnull=False,
                fecha_vencimiento__gte=hoy,
                fecha_vencimiento__lte=hoy + timedelta(days=30),
                activo__estado='activo'
            ).select_related('activo')[:10]

            # Añadir días restantes a cada software
            for software in software_por_vencer:
                software.dias_restantes = (
                    software.fecha_vencimiento - hoy).days

            # Mantenimientos recientes
            mantenimientos_recientes = Mantenimiento.objects.filter(
                fecha_realizacion__isnull=False
            ).select_related('activo').order_by('-fecha_realizacion')[:10]

            # Actividades recientes (solo si puede verlas)
            actividades = []
            if puede_ver_actividad(request.user):
                actividades = LogActividad.objects.select_related(
                    'usuario'
                ).order_by('-fecha')[:15]

            # Datos para gráficos
            departamentos_nombres = [item['departamento__nombre']
                                     for item in activos_por_departamento]
            departamentos_totales = [item['total']
                                     for item in activos_por_departamento]

            estados_nombres = [item['estado'].replace(
                '_', ' ').title() for item in activos_por_estado]
            estados_totales = [item['total'] for item in activos_por_estado]
            estados_colores = []
            for estado in activos_por_estado:
                if estado['estado'] == 'activo':
                    estados_colores.append('#28a745')
                elif estado['estado'] == 'en_mantenimiento':
                    estados_colores.append('#ffc107')
                elif estado['estado'] == 'obsoleto':
                    estados_colores.append('#dc3545')
                else:
                    estados_colores.append('#6c757d')

            # Línea temporal de adquisiciones (últimos 12 meses)
            chart_activos_meses = []
            chart_activos_totales = []

            for i in range(11, -1, -1):
                fecha = timezone.now() - timedelta(days=30*i)
                mes_nombre = fecha.strftime('%b %Y')

                # Contar activos adquiridos en ese mes
                total_mes = Activo.objects.filter(
                    id__in=list(hardware_ids) + list(software_ids),
                    fecha_adquisicion__year=fecha.year,
                    fecha_adquisicion__month=fecha.month
                ).count()

                chart_activos_meses.append(mes_nombre)
                chart_activos_totales.append(total_mes)

        except Exception as e:
            # Valores por defecto en caso de error
            total_activos = 0
            total_hardware = 0
            total_software = 0
            mantenimientos_pendientes = 0
            nivel_transformacion = 0
            activos_por_departamento = []
            software_por_vencer = []
            mantenimientos_recientes = []
            actividades = []
            departamentos_nombres = []
            departamentos_totales = []
            estados_nombres = []
            estados_totales = []
            estados_colores = []
            chart_activos_meses = []
            chart_activos_totales = []

        context = {
            'section': 'dashboard',
            'title': 'Dashboard de Reportes',
            'total_activos': total_activos,
            'total_hardware': total_hardware,
            'total_software': total_software,
            'mantenimientos_pendientes': mantenimientos_pendientes,
            'nivel_transformacion': nivel_transformacion,
            'activos_por_departamento': activos_por_departamento,
            'software_por_vencer': software_por_vencer,
            'mantenimientos_recientes': mantenimientos_recientes,
            'actividades': actividades,
            'departamentos_nombres': json.dumps(departamentos_nombres),
            'departamentos_totales': json.dumps(departamentos_totales),
            'estados_nombres': json.dumps(estados_nombres),
            'estados_totales': json.dumps(estados_totales),
            'estados_colores': json.dumps(estados_colores),
            'chart_activos_meses': json.dumps(chart_activos_meses),
            'chart_activos_totales': json.dumps(chart_activos_totales),
        }

        return render(request, 'reportes/dashboard.html', context)

    except ImportError:
        messages.error(request, 'Módulo de inventario no disponible.')
        return redirect('reportes_index')
    except Exception as e:
        messages.error(request, 'Error al cargar el dashboard de reportes.')
        return redirect('reportes_index')


# En reportes/views.py - Reemplazar la vista inventario_report_view

@supervisor_o_admin_requerido
def inventario_report_view(request):
    """Reporte de inventario - Solo supervisores y admins"""
    try:
        from inventario.models import Activo
        from usuarios.models import Departamento
        from .forms import InventarioReportForm

        form = InventarioReportForm()

        # Si es una petición POST o GET con parámetros, procesar el formulario
        if request.method == 'POST' or request.GET:
            form = InventarioReportForm(request.POST or request.GET)
            if form.is_valid():
                formato = form.cleaned_data.get('formato', 'vista')

                # Si el formato es PDF o Excel, redirigir a exportación
                if formato in ['pdf', 'excel']:
                    from django.http import QueryDict
                    params = QueryDict(mutable=True)
                    params.update(request.GET if request.method ==
                                  'GET' else request.POST)

                    # Construir URL de exportación
                    from django.urls import reverse
                    export_url = reverse('export_inventario', kwargs={
                                         'format': formato})
                    redirect_url = f"{export_url}?{params.urlencode()}"

                    return redirect(redirect_url)
                else:
                    # Para formato 'vista', ir a resultados
                    return redirect('inventario_report_result')

        context = {
            'form': form,
            'section': 'inventario_report',
            'title': 'Reporte de Inventario'
        }

        return render(request, 'reportes/inventario_report.html', context)

    except ImportError:
        messages.error(request, 'Módulo de inventario no disponible.')
        return redirect('reportes_index')


@supervisor_o_admin_requerido
def inventario_report_result_view(request):
    """Resultado del reporte de inventario - Solo supervisores y admins"""
    try:
        from inventario.models import Activo, Hardware, Software
        from .forms import InventarioReportForm

        form = InventarioReportForm(request.GET)
        activos = []

        if form.is_valid():
            # Aplicar filtros según el formulario
            queryset = Activo.objects.all()

            # Filtrar por tipo
            tipo = form.cleaned_data.get('tipo')
            if tipo == 'hardware':
                hardware_ids = Hardware.objects.values_list(
                    'activo_id', flat=True)
                queryset = queryset.filter(id__in=hardware_ids)
            elif tipo == 'software':
                software_ids = Software.objects.values_list(
                    'activo_id', flat=True)
                queryset = queryset.filter(id__in=software_ids)

            # Filtrar por departamento
            departamento = form.cleaned_data.get('departamento')
            if departamento:
                queryset = queryset.filter(departamento=departamento)

            # Filtrar por estado
            estado = form.cleaned_data.get('estado')
            if estado:
                queryset = queryset.filter(estado=estado)

            # Filtrar por fechas
            fecha_inicio = form.cleaned_data.get('fecha_inicio')
            fecha_fin = form.cleaned_data.get('fecha_fin')

            if fecha_inicio:
                queryset = queryset.filter(fecha_adquisicion__gte=fecha_inicio)
            if fecha_fin:
                queryset = queryset.filter(fecha_adquisicion__lte=fecha_fin)

            activos = queryset.select_related(
                'departamento').order_by('-fecha_adquisicion')

        context = {
            'form': form,
            'activos': activos,
            'section': 'inventario_report_result',
            'title': 'Resultado del Reporte de Inventario'
        }

        return render(request, 'reportes/inventario_report_result.html', context)

    except ImportError:
        messages.error(request, 'Módulo de inventario no disponible.')
        return redirect('reportes_index')


@supervisor_o_admin_requerido
def inventario_categoria_report_view(request):
    """Reporte de inventario por categoría - Solo supervisores y admins"""
    try:
        from inventario.models import Activo, Hardware, Software
        from django.db.models import Count

        # Obtener filtros
        tipo = request.GET.get('tipo', '')

        # Datos por departamento
        queryset = Activo.objects.exclude(estado='baja')

        if tipo == 'hardware':
            hardware_ids = Hardware.objects.values_list('activo_id', flat=True)
            queryset = queryset.filter(id__in=hardware_ids)
        elif tipo == 'software':
            software_ids = Software.objects.values_list('activo_id', flat=True)
            queryset = queryset.filter(id__in=software_ids)

        total = queryset.count()

        por_departamento = queryset.values('departamento__nombre').annotate(
            total=Count('id')
        ).order_by('-total')

        # Calcular porcentajes
        for item in por_departamento:
            item['porcentaje'] = (
                item['total'] / total * 100) if total > 0 else 0

        # Datos por estado
        por_estado = queryset.values('estado').annotate(
            total=Count('id')
        ).order_by('-total')

        for item in por_estado:
            item['porcentaje'] = (
                item['total'] / total * 100) if total > 0 else 0

        # Datos específicos según el tipo
        por_marca = []
        por_licencia = []

        if tipo == 'hardware':
            hardware_queryset = Hardware.objects.filter(
                activo__in=queryset
            )
            por_marca = hardware_queryset.values('marca').annotate(
                total=Count('id')
            ).order_by('-total')[:10]

            for item in por_marca:
                item['porcentaje'] = (
                    item['total'] / total * 100) if total > 0 else 0

        elif tipo == 'software':
            software_queryset = Software.objects.filter(
                activo__in=queryset
            )
            por_licencia = software_queryset.values('tipo_licencia').annotate(
                total=Count('id')
            ).order_by('-total')

            for item in por_licencia:
                item['porcentaje'] = (
                    item['total'] / total * 100) if total > 0 else 0

        context = {
            'tipo': tipo,
            'por_departamento': por_departamento,
            'por_estado': por_estado,
            'por_marca': por_marca,
            'por_licencia': por_licencia,
            'section': 'inventario_categoria_report',
            'title': 'Reporte por Categoría'
        }

        return render(request, 'reportes/inventario_categoria_report.html', context)

    except ImportError:
        messages.error(request, 'Módulo de inventario no disponible.')
        return redirect('reportes_index')


@supervisor_o_admin_requerido
def inventario_ubicacion_report_view(request):
    """Reporte de inventario por ubicación - Solo supervisores y admins"""
    try:
        from inventario.models import Activo, Hardware, Software
        from usuarios.models import Departamento
        from django.db.models import Count

        # Obtener filtros
        departamento_id = request.GET.get('departamento', '')

        # Datos por ubicación
        queryset = Activo.objects.exclude(estado='baja')

        if departamento_id:
            queryset = queryset.filter(departamento_id=departamento_id)

        total = queryset.count()

        por_ubicacion = queryset.values('ubicacion').annotate(
            total=Count('id')
        ).order_by('-total')

        # Calcular porcentajes
        for item in por_ubicacion:
            item['porcentaje'] = (
                item['total'] / total * 100) if total > 0 else 0

        # Datos por tipo
        hardware_ids = Hardware.objects.values_list('activo_id', flat=True)
        software_ids = Software.objects.values_list('activo_id', flat=True)

        por_tipo = []
        hardware_count = queryset.filter(id__in=hardware_ids).count()
        software_count = queryset.filter(id__in=software_ids).count()

        if hardware_count > 0:
            por_tipo.append({
                'tipo': 'hardware',
                'total': hardware_count,
                'porcentaje': (hardware_count / total * 100) if total > 0 else 0
            })

        if software_count > 0:
            por_tipo.append({
                'tipo': 'software',
                'total': software_count,
                'porcentaje': (software_count / total * 100) if total > 0 else 0
            })

        # Datos por estado
        por_estado = queryset.values('estado').annotate(
            total=Count('id')
        ).order_by('-total')

        for item in por_estado:
            item['porcentaje'] = (
                item['total'] / total * 100) if total > 0 else 0

        # Lista de departamentos para filtro
        departamentos = Departamento.objects.all().order_by('nombre')

        context = {
            'departamento_id': departamento_id,
            'departamentos': departamentos,
            'por_ubicacion': por_ubicacion,
            'por_tipo': por_tipo,
            'por_estado': por_estado,
            'section': 'inventario_ubicacion_report',
            'title': 'Reporte por Ubicación'
        }

        return render(request, 'reportes/inventario_ubicacion_report.html', context)

    except ImportError:
        messages.error(request, 'Módulo de inventario no disponible.')
        return redirect('reportes_index')


@supervisor_o_admin_requerido
def mantenimiento_report_view(request):
    """Reporte de mantenimientos - Solo supervisores y admins"""
    try:
        from inventario.models import Mantenimiento
        from .forms import MantenimientoReportForm

        form = MantenimientoReportForm()

        context = {
            'form': form,
            'section': 'mantenimiento_report',
            'title': 'Reporte de Mantenimientos'
        }

        return render(request, 'reportes/mantenimiento_report.html', context)

    except ImportError:
        messages.error(request, 'Módulo de inventario no disponible.')
        return redirect('reportes_index')


@supervisor_o_admin_requerido
def mantenimiento_report_result_view(request):
    """Resultado del reporte de mantenimientos - Solo supervisores y admins"""
    try:
        from inventario.models import Mantenimiento
        from .forms import MantenimientoReportForm
        from django.db.models import Sum, Count, Q

        form = MantenimientoReportForm(request.GET)
        mantenimientos = []
        completados = 0
        pendientes = 0
        costo_total = 0

        if form.is_valid():
            # Aplicar filtros
            queryset = Mantenimiento.objects.select_related(
                'activo', 'responsable')

            # Filtros del formulario
            tipo = form.cleaned_data.get('tipo')
            if tipo:
                queryset = queryset.filter(tipo=tipo)

            estado = form.cleaned_data.get('estado')
            if estado:
                queryset = queryset.filter(estado=estado)

            responsable = form.cleaned_data.get('responsable')
            if responsable:
                queryset = queryset.filter(responsable=responsable)

            fecha_inicio = form.cleaned_data.get('fecha_inicio')
            fecha_fin = form.cleaned_data.get('fecha_fin')

            if fecha_inicio:
                queryset = queryset.filter(fecha_programada__gte=fecha_inicio)
            if fecha_fin:
                queryset = queryset.filter(fecha_programada__lte=fecha_fin)

            mantenimientos = queryset.order_by('-fecha_programada')

            # Estadísticas
            completados = queryset.filter(estado='completado').count()
            pendientes = queryset.filter(
                Q(estado='programado') | Q(estado='en_proceso')
            ).count()

            # Costo total
            costos = queryset.aggregate(total=Sum('costo'))
            costo_total = costos['total'] or 0

        context = {
            'form': form,
            'mantenimientos': mantenimientos,
            'completados': completados,
            'pendientes': pendientes,
            'costo_total': costo_total,
            'section': 'mantenimiento_report_result',
            'title': 'Resultado del Reporte de Mantenimientos'
        }

        return render(request, 'reportes/mantenimiento_report_result.html', context)

    except ImportError:
        messages.error(request, 'Módulo de inventario no disponible.')
        return redirect('reportes_index')


@supervisor_o_admin_requerido
def obsolescencia_report_view(request):
    """Reporte de obsolescencia - Solo supervisores y admins"""
    try:
        from inventario.models import Activo, Hardware, Software
        from django.utils import timezone

        # Activos obsoletos
        activos_obsoletos = Activo.objects.filter(
            estado='obsoleto').select_related('departamento')

        # Hardware con garantía vencida
        hoy = timezone.now().date()
        hardware_garantia_vencida = Hardware.objects.filter(
            fecha_garantia__lt=hoy,
            fecha_garantia__isnull=False,
            activo__estado='activo'
        ).select_related('activo')

        # Añadir días vencidos
        for hardware in hardware_garantia_vencida:
            hardware.dias_vencido = (hoy - hardware.fecha_garantia).days

        # Software con licencia vencida
        software_licencia_vencida = Software.objects.filter(
            fecha_vencimiento__lt=hoy,
            fecha_vencimiento__isnull=False,
            activo__estado='activo'
        ).select_related('activo')

        # Añadir días vencidos
        for software in software_licencia_vencida:
            software.dias_vencido = (hoy - software.fecha_vencimiento).days

        context = {
            'activos_obsoletos': activos_obsoletos,
            'hardware_garantia_vencida': hardware_garantia_vencida,
            'software_licencia_vencida': software_licencia_vencida,
            'section': 'obsolescencia_report',
            'title': 'Reporte de Obsolescencia'
        }

        return render(request, 'reportes/obsolecia_report.html', context)

    except ImportError:
        messages.error(request, 'Módulo de inventario no disponible.')
        return redirect('reportes_index')


@supervisor_o_admin_requerido
def transformacion_digital_report_view(request):
    """Reporte de transformación digital - Solo supervisores y admins"""
    try:
        from diagnostico.models import Diagnostico, Indicador
        from .forms import TransformacionDigitalReportForm

        form = TransformacionDigitalReportForm()

        context = {
            'form': form,
            'section': 'transformacion_digital_report',
            'title': 'Reporte de Transformación Digital'
        }

        return render(request, 'reportes/transformacion_digital_report.html', context)

    except ImportError:
        context = {
            'error': 'El módulo de diagnóstico no está disponible.',
            'section': 'transformacion_digital_report',
            'title': 'Reporte de Transformación Digital'
        }
        return render(request, 'reportes/transformacion_digital_report.html', context)


@supervisor_o_admin_requerido
def transformacion_digital_report_result_view(request):
    """Resultado del reporte de transformación digital - Solo supervisores y admins"""
    try:
        from diagnostico.models import Diagnostico, Indicador
        from .forms import TransformacionDigitalReportForm
        from django.db.models import Avg

        form = TransformacionDigitalReportForm(request.GET)
        diagnosticos = []
        indicadores_por_departamento = []
        nivel_general = 0

        if form.is_valid():
            # Aplicar filtros
            queryset = Diagnostico.objects.select_related(
                'departamento', 'cuestionario', 'responsable'
            )

            departamento = form.cleaned_data.get('departamento')
            if departamento:
                queryset = queryset.filter(departamento=departamento)

            fecha_inicio = form.cleaned_data.get('fecha_inicio')
            fecha_fin = form.cleaned_data.get('fecha_fin')

            if fecha_inicio:
                queryset = queryset.filter(fecha__gte=fecha_inicio)
            if fecha_fin:
                queryset = queryset.filter(fecha__lte=fecha_fin)

            diagnosticos = queryset.order_by('-fecha')

            # Calcular nivel general
            if diagnosticos.exists():
                nivel_general = diagnosticos.aggregate(
                    promedio=Avg('nivel_general')
                )['promedio'] or 0

            # Indicadores por departamento
            if departamento:
                # Solo un departamento
                indicadores = Indicador.objects.filter(
                    diagnostico__departamento=departamento
                ).values('nombre').annotate(
                    nivel=Avg('valor')
                ).order_by('-nivel')

                indicadores_por_departamento = [{
                    'departamento': departamento.nombre,
                    'nivel': nivel_general
                }]
            else:
                # Todos los departamentos
                from usuarios.models import Departamento

                for dept in Departamento.objects.all():
                    dept_diagnosticos = diagnosticos.filter(departamento=dept)
                    if dept_diagnosticos.exists():
                        dept_nivel = dept_diagnosticos.aggregate(
                            promedio=Avg('nivel_general')
                        )['promedio'] or 0

                        indicadores_por_departamento.append({
                            'departamento': dept.nombre,
                            'nivel': dept_nivel
                        })

        context = {
            'form': form,
            'diagnosticos': diagnosticos,
            'indicadores_por_departamento': indicadores_por_departamento,
            'nivel_general': nivel_general,
            'section': 'transformacion_digital_report_result',
            'title': 'Resultado del Reporte de Transformación Digital'
        }

        return render(request, 'reportes/transformacion_digital_report_result.html', context)

    except ImportError:
        messages.error(request, 'Módulo de diagnóstico no disponible.')
        return redirect('reportes_index')


# Funciones de exportación (también protegidas)
@supervisor_o_admin_requerido
def export_inventario_view(request, format):
    print(f"Exportando {format} - Filtros: {request.GET}")
    """Exportar reporte de inventario"""
    try:
        from inventario.models import Activo, Hardware, Software
        from .forms import InventarioReportForm
        from .utils import PDFExporter, ExcelExporter, export_queryset_to_pdf, export_queryset_to_excel

        # Procesar filtros del GET request
        form = InventarioReportForm(request.GET)

        if form.is_valid():
            # Aplicar filtros según el formulario
            queryset = Activo.objects.all()

            # Filtrar por tipo
            tipo = form.cleaned_data.get('tipo')
            if tipo == 'hardware':
                hardware_ids = Hardware.objects.values_list(
                    'activo_id', flat=True)
                queryset = queryset.filter(id__in=hardware_ids)
            elif tipo == 'software':
                software_ids = Software.objects.values_list(
                    'activo_id', flat=True)
                queryset = queryset.filter(id__in=software_ids)

            # Filtrar por departamento
            departamento = form.cleaned_data.get('departamento')
            if departamento:
                queryset = queryset.filter(departamento=departamento)

            # Filtrar por estado
            estado = form.cleaned_data.get('estado')
            if estado:
                queryset = queryset.filter(estado=estado)

            # Filtrar por fechas
            fecha_inicio = form.cleaned_data.get('fecha_inicio')
            fecha_fin = form.cleaned_data.get('fecha_fin')

            if fecha_inicio:
                queryset = queryset.filter(fecha_adquisicion__gte=fecha_inicio)
            if fecha_fin:
                queryset = queryset.filter(fecha_adquisicion__lte=fecha_fin)

            queryset = queryset.select_related(
                'departamento').order_by('-fecha_adquisicion')

            # Definir campos para el reporte
            fields = [
                {'name': 'id', 'label': 'ID'},
                {'name': 'nombre', 'label': 'Nombre'},
                {'name': 'get_tipo_display', 'label': 'Tipo'},
                {'name': 'departamento.nombre', 'label': 'Departamento'},
                {'name': 'get_estado_display', 'label': 'Estado'},
                {'name': 'valor_adquisicion', 'label': 'Valor Adquisición'},
                {'name': 'fecha_adquisicion', 'label': 'Fecha Adquisición'},
            ]

            # Preparar título y filtros para el reporte
            titulo = "Reporte de Inventario"
            filtros = {}

            if tipo:
                filtros['Tipo'] = tipo.title()
            if departamento:
                filtros['Departamento'] = departamento.nombre
            if estado:
                filtros['Estado'] = estado.replace('_', ' ').title()
            if fecha_inicio:
                filtros['Fecha desde'] = fecha_inicio.strftime('%d/%m/%Y')
            if fecha_fin:
                filtros['Fecha hasta'] = fecha_fin.strftime('%d/%m/%Y')

            # Generar reporte según formato
            if format.lower() == 'pdf':
                return export_queryset_to_pdf(
                    queryset=queryset,
                    fields=fields,
                    title=titulo,
                    filters=filtros,
                    landscape=True
                )
            elif format.lower() == 'excel':
                return export_queryset_to_excel(
                    queryset=queryset,
                    fields=fields,
                    title=titulo,
                    filters=filtros
                )
            else:
                messages.error(request, 'Formato de exportación no válido.')
                return redirect('inventario_report')
        else:
            messages.error(request, 'Error en los filtros del reporte.')
            return redirect('inventario_report')

    except ImportError as e:
        messages.error(
            request, f'Error: Dependencias faltantes para exportación. {str(e)}')
        return redirect('inventario_report')
    except Exception as e:
        messages.error(request, f'Error al generar el reporte: {str(e)}')
        return redirect('inventario_report')


@supervisor_o_admin_requerido
def export_mantenimiento_view(request, format):
    print(f"Exportando {format} - Filtros: {request.GET}")
    """Exportar reporte de mantenimientos"""
    try:
        from inventario.models import Mantenimiento
        from .forms import MantenimientoReportForm
        from .utils import export_queryset_to_pdf, export_queryset_to_excel

        # Procesar filtros del GET request
        form = MantenimientoReportForm(request.GET)

        if form.is_valid():
            # Aplicar filtros
            queryset = Mantenimiento.objects.select_related(
                'activo', 'responsable')

            # Filtros del formulario
            tipo = form.cleaned_data.get('tipo')
            if tipo:
                queryset = queryset.filter(tipo=tipo)

            estado = form.cleaned_data.get('estado')
            if estado:
                queryset = queryset.filter(estado=estado)

            responsable = form.cleaned_data.get('responsable')
            if responsable:
                queryset = queryset.filter(responsable=responsable)

            fecha_inicio = form.cleaned_data.get('fecha_inicio')
            fecha_fin = form.cleaned_data.get('fecha_fin')

            if fecha_inicio:
                queryset = queryset.filter(fecha_programada__gte=fecha_inicio)
            if fecha_fin:
                queryset = queryset.filter(fecha_programada__lte=fecha_fin)

            queryset = queryset.order_by('-fecha_programada')

            # Definir campos para el reporte
            fields = [
                {'name': 'id', 'label': 'ID'},
                {'name': 'activo.nombre', 'label': 'Activo'},
                {'name': 'get_tipo_display', 'label': 'Tipo'},
                {'name': 'fecha_programada', 'label': 'Fecha Programada'},
                {'name': 'fecha_realizacion', 'label': 'Fecha Realización'},
                {'name': 'responsable.get_full_name', 'label': 'Responsable'},
                {'name': 'get_estado_display', 'label': 'Estado'},
                {'name': 'costo', 'label': 'Costo'},
                {'name': 'descripcion', 'label': 'Descripción'},
            ]

            # Preparar título y filtros para el reporte
            titulo = "Reporte de Mantenimientos"
            filtros = {}

            if tipo:
                filtros['Tipo'] = tipo.title()
            if estado:
                filtros['Estado'] = estado.replace('_', ' ').title()
            if responsable:
                filtros['Responsable'] = responsable.get_full_name()
            if fecha_inicio:
                filtros['Fecha desde'] = fecha_inicio.strftime('%d/%m/%Y')
            if fecha_fin:
                filtros['Fecha hasta'] = fecha_fin.strftime('%d/%m/%Y')

            # Generar reporte según formato
            if format.lower() == 'pdf':
                return export_queryset_to_pdf(
                    queryset=queryset,
                    fields=fields,
                    title=titulo,
                    filters=filtros,
                    landscape=True
                )
            elif format.lower() == 'excel':
                return export_queryset_to_excel(
                    queryset=queryset,
                    fields=fields,
                    title=titulo,
                    filters=filtros
                )
            else:
                messages.error(request, 'Formato de exportación no válido.')
                return redirect('mantenimiento_report')
        else:
            messages.error(request, 'Error en los filtros del reporte.')
            return redirect('mantenimiento_report')

    except ImportError as e:
        messages.error(
            request, f'Error: Dependencias faltantes para exportación. {str(e)}')
        return redirect('mantenimiento_report')
    except Exception as e:
        messages.error(request, f'Error al generar el reporte: {str(e)}')
        return redirect('mantenimiento_report')


@supervisor_o_admin_requerido
def export_diagnostico_view(request, format):
    print(f"Exportando {format} - Filtros: {request.GET}")
    """Exportar reporte de diagnóstico"""
    try:
        from diagnostico.models import Diagnostico
        from .forms import TransformacionDigitalReportForm
        from .utils import export_queryset_to_pdf, export_queryset_to_excel

        # Procesar filtros del GET request
        form = TransformacionDigitalReportForm(request.GET)

        if form.is_valid():
            # Aplicar filtros
            queryset = Diagnostico.objects.select_related(
                'departamento', 'cuestionario', 'responsable'
            )

            departamento = form.cleaned_data.get('departamento')
            if departamento:
                queryset = queryset.filter(departamento=departamento)

            fecha_inicio = form.cleaned_data.get('fecha_inicio')
            fecha_fin = form.cleaned_data.get('fecha_fin')

            if fecha_inicio:
                queryset = queryset.filter(fecha__gte=fecha_inicio)
            if fecha_fin:
                queryset = queryset.filter(fecha__lte=fecha_fin)

            queryset = queryset.order_by('-fecha')

            # Definir campos para el reporte
            fields = [
                {'name': 'id', 'label': 'ID'},
                {'name': 'departamento.nombre', 'label': 'Departamento'},
                {'name': 'cuestionario.titulo', 'label': 'Cuestionario'},
                {'name': 'fecha', 'label': 'Fecha'},
                {'name': 'nivel_general', 'label': 'Nivel General'},
                {'name': 'responsable.get_full_name', 'label': 'Responsable'},
                {'name': 'observaciones', 'label': 'Observaciones'},
            ]

            # Preparar título y filtros para el reporte
            titulo = "Reporte de Transformación Digital"
            filtros = {}

            if departamento:
                filtros['Departamento'] = departamento.nombre
            if fecha_inicio:
                filtros['Fecha desde'] = fecha_inicio.strftime('%d/%m/%Y')
            if fecha_fin:
                filtros['Fecha hasta'] = fecha_fin.strftime('%d/%m/%Y')

            # Generar reporte según formato
            if format.lower() == 'pdf':
                return export_queryset_to_pdf(
                    queryset=queryset,
                    fields=fields,
                    title=titulo,
                    filters=filtros,
                    landscape=True
                )
            elif format.lower() == 'excel':
                return export_queryset_to_excel(
                    queryset=queryset,
                    fields=fields,
                    title=titulo,
                    filters=filtros
                )
            else:
                messages.error(request, 'Formato de exportación no válido.')
                return redirect('transformacion_digital_report')
        else:
            messages.error(request, 'Error en los filtros del reporte.')
            return redirect('transformacion_digital_report')

    except ImportError as e:
        messages.error(
            request, f'Error: Módulo de diagnóstico no disponible. {str(e)}')
        return redirect('transformacion_digital_report')
    except Exception as e:
        messages.error(request, f'Error al generar el reporte: {str(e)}')
        return redirect('transformacion_digital_report')


@supervisor_o_admin_requerido
def index(request):
    """Vista de compatibilidad - redirige a reportes_index_view"""
    return reportes_index_view(request)


# Función auxiliar para verificar acceso a reportes en middleware
def verificar_acceso_reportes(request):
    """
    Función auxiliar que puede ser usada en middleware o context processors
    """
    if not request.user.is_authenticated:
        return False

    return puede_ver_reportes(request.user)
