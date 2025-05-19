# reportes/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.db.models import Count, Avg, Sum, Q
from django.utils import timezone
import json
import csv
import io
import xlsxwriter
from datetime import datetime, timedelta
from .models import Reporte, ConfiguracionDashboard
from .forms import (
    ReporteForm, InventarioReportForm, MantenimientoReportForm,
    TransformacionDigitalReportForm, DashboardConfigForm
)
from inventario.models import Activo, Hardware, Software, Mantenimiento
from usuarios.models import Departamento, LogActividad
from diagnostico.models import Diagnostico, IndicadorDiagnostico


@login_required
def index(request):
    """Vista principal del módulo de reportes"""
    return render(request, 'reportes/index.html')


@login_required
def inventario_report(request):
    """Reporte general de inventario"""
    if request.method == 'GET' and request.GET:
        form = InventarioReportForm(request.GET)
        if form.is_valid():
            tipo = form.cleaned_data['tipo']
            departamento = form.cleaned_data['departamento']
            estado = form.cleaned_data['estado']
            fecha_inicio = form.cleaned_data['fecha_inicio']
            fecha_fin = form.cleaned_data['fecha_fin']
            formato = form.cleaned_data['formato']

            # Filtrar activos
            activos = Activo.objects.all()

            if tipo:
                activos = activos.filter(tipo=tipo)
            if departamento:
                activos = activos.filter(departamento=departamento)
            if estado:
                activos = activos.filter(estado=estado)
            if fecha_inicio:
                activos = activos.filter(fecha_adquisicion__gte=fecha_inicio)
            if fecha_fin:
                activos = activos.filter(fecha_adquisicion__lte=fecha_fin)

            # Ordenar por fecha de adquisición
            activos = activos.order_by('-fecha_adquisicion')

            # Registrar actividad
            LogActividad.objects.create(
                usuario=request.user,
                accion=f"Generación de reporte de inventario",
                detalles=f"Formato: {formato}, Total registros: {activos.count()}"
            )

            # Exportar en diferentes formatos
            if formato != 'html':
                return export_inventario(request, formato, activos)

            # Guardar reporte
            Reporte.objects.create(
                nombre=f"Reporte de Inventario {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                tipo='inventario',
                usuario=request.user,
                formato=formato,
                parametros=json.dumps(request.GET)
            )

            return render(request, 'reportes/inventario_report_result.html', {
                'activos': activos,
                'form': form
            })
    else:
        form = InventarioReportForm()

    return render(request, 'reportes/inventario_report.html', {'form': form})


@login_required
def inventario_categoria_report(request):
    """Reporte de inventario por categoría"""
    tipo = request.GET.get('tipo', '')

    # Filtrar activos
    activos = Activo.objects.all()

    if tipo:
        activos = activos.filter(tipo=tipo)

    # Agrupar por departamento
    por_departamento = activos.values('departamento__nombre').annotate(
        total=Count('id')
    ).order_by('-total')

    # Agrupar por estado
    por_estado = activos.values('estado').annotate(
        total=Count('id')
    ).order_by('-total')

    # Registrar actividad
    LogActividad.objects.create(
        usuario=request.user,
        accion=f"Generación de reporte de inventario por categoría",
        detalles=f"Tipo: {tipo if tipo else 'Todos'}"
    )

    return render(request, 'reportes/inventario_categoria_report.html', {
        'por_departamento': por_departamento,
        'por_estado': por_estado,
        'tipo': tipo
    })


@login_required
def inventario_ubicacion_report(request):
    """Reporte de inventario por ubicación"""
    departamento_id = request.GET.get('departamento', '')

    # Filtrar activos
    activos = Activo.objects.all()

    if departamento_id:
        activos = activos.filter(departamento_id=departamento_id)

    # Agrupar por ubicación
    por_ubicacion = activos.values('ubicacion').annotate(
        total=Count('id')
    ).order_by('-total')

    # Registrar actividad
    LogActividad.objects.create(
        usuario=request.user,
        accion=f"Generación de reporte de inventario por ubicación",
        detalles=f"Departamento: {departamento_id if departamento_id else 'Todos'}"
    )

    return render(request, 'reportes/inventario_ubicacion_report.html', {
        'por_ubicacion': por_ubicacion,
        'departamento_id': departamento_id,
        'departamentos': Departamento.objects.all()
    })


@login_required
def mantenimiento_report(request):
    """Reporte de mantenimientos"""
    if request.method == 'GET' and request.GET:
        form = MantenimientoReportForm(request.GET)
        if form.is_valid():
            tipo = form.cleaned_data['tipo']
            estado = form.cleaned_data['estado']
            fecha_inicio = form.cleaned_data['fecha_inicio']
            fecha_fin = form.cleaned_data['fecha_fin']
            responsable = form.cleaned_data['responsable']
            formato = form.cleaned_data['formato']

            # Filtrar mantenimientos
            mantenimientos = Mantenimiento.objects.all().select_related('activo', 'responsable')

            if tipo:
                mantenimientos = mantenimientos.filter(tipo=tipo)
            if estado:
                mantenimientos = mantenimientos.filter(estado=estado)
            if fecha_inicio:
                mantenimientos = mantenimientos.filter(
                    fecha_programada__gte=fecha_inicio)
            if fecha_fin:
                mantenimientos = mantenimientos.filter(
                    fecha_programada__lte=fecha_fin)
            if responsable:
                mantenimientos = mantenimientos.filter(responsable=responsable)

            # Ordenar por fecha programada
            mantenimientos = mantenimientos.order_by('fecha_programada')

            # Registrar actividad
            LogActividad.objects.create(
                usuario=request.user,
                accion=f"Generación de reporte de mantenimientos",
                detalles=f"Formato: {formato}, Total registros: {mantenimientos.count()}"
            )

            # Exportar en diferentes formatos
            if formato != 'html':
                return export_mantenimiento(request, formato, mantenimientos)

            # Guardar reporte
            Reporte.objects.create(
                nombre=f"Reporte de Mantenimientos {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                tipo='mantenimiento',
                usuario=request.user,
                formato=formato,
                parametros=json.dumps(request.GET)
            )

            return render(request, 'reportes/mantenimiento_report_result.html', {
                'mantenimientos': mantenimientos,
                'form': form
            })
    else:
        form = MantenimientoReportForm()

    return render(request, 'reportes/mantenimiento_report.html', {'form': form})


@login_required
def obsolescencia_report(request):
    """Reporte de obsolescencia"""
    # Activos obsoletos o próximos a serlo
    activos_obsoletos = Activo.objects.filter(estado='obsoleto')

    # Hardware con garantía vencida
    hoy = timezone.now().date()
    hardware_garantia_vencida = Hardware.objects.filter(
        Q(fecha_garantia__isnull=False) & Q(fecha_garantia__lt=hoy)
    ).select_related('activo')

    # Software con licencia vencida
    software_licencia_vencida = Software.objects.filter(
        Q(fecha_vencimiento__isnull=False) & Q(fecha_vencimiento__lt=hoy)
    ).select_related('activo')

    # Registrar actividad
    LogActividad.objects.create(
        usuario=request.user,
        accion=f"Generación de reporte de obsolescencia",
        detalles=f"Activos obsoletos: {activos_obsoletos.count()}"
    )

    return render(request, 'reportes/obsolescencia_report.html', {
        'activos_obsoletos': activos_obsoletos,
        'hardware_garantia_vencida': hardware_garantia_vencida,
        'software_licencia_vencida': software_licencia_vencida
    })


@login_required
def transformacion_digital_report(request):
    """Reporte de transformación digital"""
    if request.method == 'GET' and request.GET:
        form = TransformacionDigitalReportForm(request.GET)
        if form.is_valid():
            departamento = form.cleaned_data['departamento']
            fecha_inicio = form.cleaned_data['fecha_inicio']
            fecha_fin = form.cleaned_data['fecha_fin']
            formato = form.cleaned_data['formato']

            # Filtrar diagnósticos
            diagnosticos = Diagnostico.objects.all().select_related(
                'departamento', 'responsable', 'cuestionario')

            if departamento:
                diagnosticos = diagnosticos.filter(departamento=departamento)
            if fecha_inicio:
                diagnosticos = diagnosticos.filter(fecha__gte=fecha_inicio)
            if fecha_fin:
                diagnosticos = diagnosticos.filter(fecha__lte=fecha_fin)

            # Ordenar por fecha
            diagnosticos = diagnosticos.order_by('-fecha')

            # Indicadores agregados
            nivel_general = diagnosticos.aggregate(
                avg=Avg('nivel_general'))['avg']

            # Indicadores por departamento
            indicadores_por_departamento = []
            for depto in Departamento.objects.all():
                diags = diagnosticos.filter(departamento=depto)
                if diags.exists():
                    nivel = diags.aggregate(avg=Avg('nivel_general'))['avg']
                    indicadores_por_departamento.append({
                        'departamento': depto.nombre,
                        'nivel': nivel
                    })

            # Registrar actividad
            LogActividad.objects.create(
                usuario=request.user,
                accion=f"Generación de reporte de transformación digital",
                detalles=f"Formato: {formato}, Total diagnósticos: {diagnosticos.count()}"
            )

            # Exportar en diferentes formatos
            if formato != 'html':
                return export_diagnostico(request, formato, diagnosticos, nivel_general, indicadores_por_departamento)

            # Guardar reporte
            Reporte.objects.create(
                nombre=f"Reporte de Transformación Digital {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                tipo='diagnostico',
                usuario=request.user,
                formato=formato,
                parametros=json.dumps(request.GET)
            )

            return render(request, 'reportes/transformacion_digital_report_result.html', {
                'diagnosticos': diagnosticos,
                'nivel_general': nivel_general,
                'indicadores_por_departamento': indicadores_por_departamento,
                'form': form
            })
    else:
        form = TransformacionDigitalReportForm()

    return render(request, 'reportes/transformacion_digital_report.html', {'form': form})


@login_required
def dashboard(request):
    """Dashboard con gráficos y resúmenes"""
    # Resumen de activos
    total_activos = Activo.objects.count()
    total_hardware = Hardware.objects.count()
    total_software = Software.objects.count()

    # Activos por departamento
    activos_por_departamento = Activo.objects.values('departamento__nombre').annotate(
        total=Count('id')
    ).order_by('-total')[:5]

    # Activos por estado
    activos_por_estado = Activo.objects.values('estado').annotate(
        total=Count('id')
    ).order_by('-total')

    # Mantenimientos pendientes
    mantenimientos_pendientes = Mantenimiento.objects.filter(
        Q(estado='programado') | Q(estado='en_proceso')
    ).count()

    # Mantenimientos recientes
    mantenimientos_recientes = Mantenimiento.objects.filter(
        fecha_realizacion__isnull=False
    ).order_by('-fecha_realizacion')[:5]

    # Software por vencer
    hoy = timezone.now().date()
    treinta_dias = hoy + timedelta(days=30)
    software_por_vencer = Software.objects.filter(
        fecha_vencimiento__isnull=False,
        fecha_vencimiento__gt=hoy,
        fecha_vencimiento__lte=treinta_dias
    ).select_related('activo').order_by('fecha_vencimiento')

    # Nivel de transformación digital
    nivel_transformacion = Diagnostico.objects.aggregate(
        avg=Avg('nivel_general'))['avg']

    # Registrar actividad
    LogActividad.objects.create(
        usuario=request.user,
        accion=f"Consulta de dashboard",
        detalles=f"Total activos: {total_activos}"
    )

    return render(request, 'reportes/dashboard.html', {
        'total_activos': total_activos,
        'total_hardware': total_hardware,
        'total_software': total_software,
        'activos_por_departamento': activos_por_departamento,
        'activos_por_estado': activos_por_estado,
        'mantenimientos_pendientes': mantenimientos_pendientes,
        'mantenimientos_recientes': mantenimientos_recientes,
        'software_por_vencer': software_por_vencer,
        'nivel_transformacion': nivel_transformacion
    })

# Funciones de exportación


@login_required
def export_inventario(request, format, activos=None):
    """Exportar reporte de inventario"""
    if activos is None:
        # Si no se proporciona un queryset, obtener activos de los parámetros de la solicitud
        tipo = request.GET.get('tipo', '')
        departamento_id = request.GET.get('departamento', '')
        estado = request.GET.get('estado', '')
        fecha_inicio = request.GET.get('fecha_inicio', '')
        fecha_fin = request.GET.get('fecha_fin', '')

        activos = Activo.objects.all()

        if tipo:
            activos = activos.filter(tipo=tipo)
        if departamento_id:
            activos = activos.filter(departamento_id=departamento_id)
        if estado:
            activos = activos.filter(estado=estado)
        if fecha_inicio:
            activos = activos.filter(fecha_adquisicion__gte=fecha_inicio)
        if fecha_fin:
            activos = activos.filter(fecha_adquisicion__lte=fecha_fin)

    # Generar reporte en formato CSV
    if format == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="inventario.csv"'

        writer = csv.writer(response)
        writer.writerow(['ID', 'Nombre', 'Tipo', 'Departamento',
                        'Estado', 'Valor de Adquisición', 'Fecha de Adquisición'])

        for activo in activos:
            writer.writerow([
                activo.id,
                activo.nombre,
                activo.get_tipo_display(),
                activo.departamento.nombre if activo.departamento else '',
                activo.get_estado_display(),
                activo.valor_adquisicion,
                activo.fecha_adquisicion
            ])

        return response

    # Generar reporte en formato Excel
    elif format == 'excel':
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet()

        # Agregar encabezados
        headers = ['ID', 'Nombre', 'Tipo', 'Departamento', 'Estado',
                   'Valor de Adquisición', 'Fecha de Adquisición']
        for col, header in enumerate(headers):
            worksheet.write(0, col, header)

        # Agregar datos
        for row, activo in enumerate(activos, 1):
            worksheet.write(row, 0, activo.id)
            worksheet.write(row, 1, activo.nombre)
            worksheet.write(row, 2, activo.get_tipo_display())
            worksheet.write(
                row, 3, activo.departamento.nombre if activo.departamento else '')
            worksheet.write(row, 4, activo.get_estado_display())
            worksheet.write(row, 5, float(activo.valor_adquisicion))
            worksheet.write(
                row, 6, activo.fecha_adquisicion.strftime('%Y-%m-%d'))

        workbook.close()
        output.seek(0)

        response = HttpResponse(output.read(
        ), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="inventario.xlsx"'

        return response

    # Generar reporte en formato PDF (simplificado para este ejemplo)
    elif format == 'pdf':
        # En un caso real, usaríamos una biblioteca como ReportLab o WeasyPrint
        # Para este ejemplo, mostraremos un mensaje
        return HttpResponse("Funcionalidad de exportación a PDF en desarrollo", content_type='text/plain')

    # Formato no soportado
    else:
        return HttpResponse("Formato no soportado", content_type='text/plain')


@login_required
def export_mantenimiento(request, format, mantenimientos=None):
    """Exportar reporte de mantenimiento"""
    if mantenimientos is None:
        # Si no se proporciona un queryset, obtener mantenimientos de los parámetros de la solicitud
        tipo = request.GET.get('tipo', '')
        estado = request.GET.get('estado', '')
        fecha_inicio = request.GET.get('fecha_inicio', '')
        fecha_fin = request.GET.get('fecha_fin', '')
        responsable_id = request.GET.get('responsable', '')

        mantenimientos = Mantenimiento.objects.all().select_related('activo', 'responsable')

        if tipo:
            mantenimientos = mantenimientos.filter(tipo=tipo)
        if estado:
            mantenimientos = mantenimientos.filter(estado=estado)
        if fecha_inicio:
            mantenimientos = mantenimientos.filter(
                fecha_programada__gte=fecha_inicio)
        if fecha_fin:
            mantenimientos = mantenimientos.filter(
                fecha_programada__lte=fecha_fin)
        if responsable_id:
            mantenimientos = mantenimientos.filter(
                responsable_id=responsable_id)

    # Generar reporte en formato CSV
    if format == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="mantenimientos.csv"'

        writer = csv.writer(response)
        writer.writerow(['ID', 'Activo', 'Tipo', 'Fecha Programada',
                        'Fecha Realización', 'Responsable', 'Estado', 'Costo'])

        for mantenimiento in mantenimientos:
            writer.writerow([
                mantenimiento.id,
                mantenimiento.activo.nombre,
                mantenimiento.get_tipo_display(),
                mantenimiento.fecha_programada,
                mantenimiento.fecha_realizacion if mantenimiento.fecha_realizacion else '',
                mantenimiento.responsable.get_full_name() if mantenimiento.responsable else '',
                mantenimiento.get_estado_display(),
                mantenimiento.costo if mantenimiento.costo else ''
            ])

        return response

    # Generar reporte en formato Excel
    elif format == 'excel':
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet()

        # Agregar encabezados
        headers = ['ID', 'Activo', 'Tipo', 'Fecha Programada',
                   'Fecha Realización', 'Responsable', 'Estado', 'Costo']
        for col, header in enumerate(headers):
            worksheet.write(0, col, header)

        # Agregar datos
        for row, mantenimiento in enumerate(mantenimientos, 1):
            worksheet.write(row, 0, mantenimiento.id)
            worksheet.write(row, 1, mantenimiento.activo.nombre)
            worksheet.write(row, 2, mantenimiento.get_tipo_display())
            worksheet.write(
                row, 3, mantenimiento.fecha_programada.strftime('%Y-%m-%d'))
            if mantenimiento.fecha_realizacion:
                worksheet.write(
                    row, 4, mantenimiento.fecha_realizacion.strftime('%Y-%m-%d'))
            else:
                worksheet.write(row, 4, '')
            worksheet.write(row, 5, mantenimiento.responsable.get_full_name(
            ) if mantenimiento.responsable else '')
            worksheet.write(row, 6, mantenimiento.get_estado_display())
            if mantenimiento.costo:
                worksheet.write(row, 7, float(mantenimiento.costo))
            else:
                worksheet.write(row, 7, '')

        workbook.close()
        output.seek(0)

        response = HttpResponse(output.read(
        ), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="mantenimientos.xlsx"'

        return response

    # Generar reporte en formato PDF (simplificado para este ejemplo)
    elif format == 'pdf':
        # En un caso real, usaríamos una biblioteca como ReportLab o WeasyPrint
        # Para este ejemplo, mostraremos un mensaje
        return HttpResponse("Funcionalidad de exportación a PDF en desarrollo", content_type='text/plain')

    # Formato no soportado
    else:
        return HttpResponse("Formato no soportado", content_type='text/plain')


@login_required
def export_diagnostico(request, format, diagnosticos=None, nivel_general=None, indicadores_por_departamento=None):
    """Exportar reporte de diagnóstico"""
    if diagnosticos is None:
        # Si no se proporciona un queryset, obtener diagnósticos de los parámetros de la solicitud
        departamento_id = request.GET.get('departamento', '')
        fecha_inicio = request.GET.get('fecha_inicio', '')
        fecha_fin = request.GET.get('fecha_fin', '')

        diagnosticos = Diagnostico.objects.all().select_related(
            'departamento', 'responsable', 'cuestionario')

        if departamento_id:
            diagnosticos = diagnosticos.filter(departamento_id=departamento_id)
        if fecha_inicio:
            diagnosticos = diagnosticos.filter(fecha__gte=fecha_inicio)
        if fecha_fin:
            diagnosticos = diagnosticos.filter(fecha__lte=fecha_fin)

        nivel_general = diagnosticos.aggregate(avg=Avg('nivel_general'))['avg']

        indicadores_por_departamento = []
        for depto in Departamento.objects.all():
            diags = diagnosticos.filter(departamento=depto)
            if diags.exists():
                nivel = diags.aggregate(avg=Avg('nivel_general'))['avg']
                indicadores_por_departamento.append({
                    'departamento': depto.nombre,
                    'nivel': nivel
                })

    # Generar reporte en formato CSV
    if format == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="diagnosticos.csv"'

        writer = csv.writer(response)
        writer.writerow(['ID', 'Departamento', 'Fecha',
                        'Cuestionario', 'Nivel General', 'Responsable'])

        for diagnostico in diagnosticos:
            writer.writerow([
                diagnostico.id,
                diagnostico.departamento.nombre,
                diagnostico.fecha,
                diagnostico.cuestionario.titulo,
                diagnostico.nivel_general,
                diagnostico.responsable.get_full_name() if diagnostico.responsable else ''
            ])

        writer.writerow([])
        writer.writerow(['Indicadores por Departamento'])
        writer.writerow(['Departamento', 'Nivel'])

        for indicador in indicadores_por_departamento:
            writer.writerow([
                indicador['departamento'],
                indicador['nivel']
            ])

        return response

    # Generar reporte en formato Excel
    elif format == 'excel':
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet()

        # Agregar encabezados
        headers = ['ID', 'Departamento', 'Fecha',
                   'Cuestionario', 'Nivel General', 'Responsable']
        for col, header in enumerate(headers):
            worksheet.write(0, col, header)

        # Agregar datos
        for row, diagnostico in enumerate(diagnosticos, 1):
            worksheet.write(row, 0, diagnostico.id)
            worksheet.write(row, 1, diagnostico.departamento.nombre)
            worksheet.write(row, 2, diagnostico.fecha.strftime('%Y-%m-%d'))
            worksheet.write(row, 3, diagnostico.cuestionario.titulo)
            worksheet.write(row, 4, float(diagnostico.nivel_general)
                            if diagnostico.nivel_general else 0)
            worksheet.write(row, 5, diagnostico.responsable.get_full_name(
            ) if diagnostico.responsable else '')

        # Agregar indicadores por departamento en una nueva hoja
        worksheet_indicadores = workbook.add_worksheet('Indicadores')
        worksheet_indicadores.write(0, 0, 'Departamento')
        worksheet_indicadores.write(0, 1, 'Nivel')

        for row, indicador in enumerate(indicadores_por_departamento, 1):
            worksheet_indicadores.write(row, 0, indicador['departamento'])
            worksheet_indicadores.write(row, 1, float(
                indicador['nivel']) if indicador['nivel'] else 0)

        workbook.close()
        output.seek(0)

        response = HttpResponse(output.read(
        ), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="diagnosticos.xlsx"'

        return response

    # Generar reporte en formato PDF (simplificado para este ejemplo)
    elif format == 'pdf':
        # En un caso real, usaríamos una biblioteca como ReportLab o WeasyPrint
        # Para este ejemplo, mostraremos un mensaje
        return HttpResponse("Funcionalidad de exportación a PDF en desarrollo", content_type='text/plain')

    # Formato no soportado
    else:
        return HttpResponse("Formato no soportado", content_type='text/plain')
