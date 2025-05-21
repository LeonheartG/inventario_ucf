# reportes/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum, Avg, F, Q, Value
from django.db.models.functions import TruncMonth
from django.utils import timezone
from datetime import timedelta
from django.http import HttpResponse
import csv
import json
from io import BytesIO
import os

# Importaciones de modelos
from inventario.models import Activo, Hardware, Software, Mantenimiento
from locales.models import Local, Equipamiento
from usuarios.models import Departamento
from diagnostico.models import Diagnostico, IndicadorDiagnostico as Indicador

# Librerías para exportación
try:
    import xlsxwriter
except ImportError:
    xlsxwriter = None

try:
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Image, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, landscape
    from reportlab.lib.units import inch
except ImportError:
    reportlab = None


@login_required
def index(request):
    """Vista principal del módulo de reportes"""
    return render(request, 'reportes/index.html')


@login_required
def dashboard(request):
    """Dashboard principal con indicadores clave"""
    # Datos para el dashboard - mejorar conteo de activos
    hardware_ids = Hardware.objects.values_list('activo_id', flat=True)
    software_ids = Software.objects.values_list('activo_id', flat=True)
    valid_ids = list(hardware_ids) + list(software_ids)

    # Contar solo activos válidos y no dados de baja
    total_activos = Activo.objects.filter(
        id__in=valid_ids
    ).exclude(
        estado='baja'
    ).count()

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

    # Activos por departamento - mejorar filtrado
    activos_por_departamento = Activo.objects.filter(
        id__in=valid_ids
    ).exclude(
        estado='baja'
    ).values(
        'departamento__nombre'
    ).annotate(
        total=Count('id'),
        porcentaje=Count('id') * 100.0 / total_activos if total_activos else 0
    ).order_by('-total')

    # Activos por estado - mejorar filtrado
    activos_por_estado = Activo.objects.filter(
        id__in=valid_ids
    ).values(
        'estado'
    ).annotate(
        total=Count('id'),
        porcentaje=Count('id') * 100.0 / total_activos if total_activos else 0
    ).order_by('-total')

    # Software por vencer (próximos 30 días)
    hoy = timezone.now().date()
    treinta_dias = hoy + timedelta(days=30)
    software_por_vencer = Software.objects.filter(
        fecha_vencimiento__isnull=False,
        fecha_vencimiento__gte=hoy,
        fecha_vencimiento__lte=treinta_dias,
        # Solo contar activos válidos
        activo__estado__in=['activo', 'en_mantenimiento']
    ).select_related('activo').order_by('fecha_vencimiento')

    # Añadir días restantes
    for software in software_por_vencer:
        software.dias_restantes = (software.fecha_vencimiento - hoy).days

    # Mantenimientos recientes
    mantenimientos_recientes = Mantenimiento.objects.filter(
        estado='completado',
        fecha_realizacion__isnull=False
    ).select_related('activo').order_by('-fecha_realizacion')[:5]

    # Logs de actividad reciente
    try:
        from usuarios.models import LogActividad
        actividades = LogActividad.objects.select_related(
            'usuario').order_by('-fecha')[:10]
    except ImportError:
        actividades = []

    # Nivel de transformación digital
    try:
        nivel_transformacion = Diagnostico.objects.aggregate(
            Avg('nivel_general'))['nivel_general__avg'] or 0
    except:
        nivel_transformacion = 0

    # Datos para gráficos - mejorar filtrado
    # Crear datos para gráfico de activos por mes
    activos_por_mes = Activo.objects.filter(
        id__in=valid_ids
    ).exclude(
        estado='baja'
    ).annotate(
        mes=TruncMonth('fecha_adquisicion')
    ).values('mes').annotate(
        total=Count('id')
    ).order_by('mes')

    # Convertir a formato para Chart.js
    chart_activos_meses = []
    chart_activos_totales = []

    for item in activos_por_mes:
        if item['mes']:
            chart_activos_meses.append(item['mes'].strftime('%b %Y'))
            chart_activos_totales.append(item['total'])

    # Preparar datos para JavaScript
    # Department data: Create arrays for names and totals
    departamentos_nombres = []
    departamentos_totales = []

    for item in activos_por_departamento:
        departamentos_nombres.append(item['departamento__nombre'])
        departamentos_totales.append(item['total'])

    # Status data: Create arrays for names, totals, and colors
    estados_nombres = []
    estados_totales = []
    estados_colores = []

    for item in activos_por_estado:
        if item['estado'] == 'activo':
            estados_nombres.append('Activo')
            estados_colores.append('#28a745')
        elif item['estado'] == 'en_mantenimiento':
            estados_nombres.append('En Mantenimiento')
            estados_colores.append('#ffc107')
        elif item['estado'] == 'obsoleto':
            estados_nombres.append('Obsoleto')
            estados_colores.append('#dc3545')
        elif item['estado'] == 'baja':
            estados_nombres.append('De Baja')
            estados_colores.append('#6c757d')
        else:
            estados_nombres.append(item['estado'])
            estados_colores.append('#6c757d')  # Default color

        estados_totales.append(item['total'])

    context = {
        'total_activos': total_activos,
        'total_hardware': total_hardware,
        'total_software': total_software,
        'mantenimientos_pendientes': mantenimientos_pendientes,
        'activos_por_departamento': activos_por_departamento,
        'activos_por_estado': activos_por_estado,
        'software_por_vencer': software_por_vencer,
        'mantenimientos_recientes': mantenimientos_recientes,
        'actividades': actividades,
        'nivel_transformacion': nivel_transformacion,
        # Datos para gráficos
        'chart_activos_meses': json.dumps(chart_activos_meses),
        'chart_activos_totales': json.dumps(chart_activos_totales),

        # Add these new JSONified arrays for JavaScript
        'departamentos_nombres': json.dumps(departamentos_nombres),
        'departamentos_totales': json.dumps(departamentos_totales),
        'estados_nombres': json.dumps(estados_nombres),
        'estados_totales': json.dumps(estados_totales),
        'estados_colores': json.dumps(estados_colores),
    }

    return render(request, 'reportes/dashboard.html', context)


@login_required
def inventario_report(request):
    """Página para generar reporte de inventario"""
    from .forms import InventarioReportForm

    if request.method == 'GET' and any(param for param in request.GET if param not in ['page']):
        # Si hay parámetros en la URL, procesar el formulario
        form = InventarioReportForm(request.GET)
        if form.is_valid():
            # Exportar directamente en el formato seleccionado
            formato = form.cleaned_data.get('formato', 'pdf')
            return export_inventario(request, format=formato)
    else:
        # Si no hay parámetros, mostrar formulario vacío
        form = InventarioReportForm()

    context = {
        'form': form
    }

    return render(request, 'reportes/inventario_report.html', context)


@login_required
def inventario_report_result(request):
    """Resultados del reporte de inventario"""
    from .forms import InventarioReportForm

    # Obtener parámetros del formulario
    form = InventarioReportForm(request.GET)

    # Filtrar activos
    activos = Activo.objects.all().select_related('departamento')

    if form.is_valid():
        # Aplicar filtros si el formulario es válido
        tipo = form.cleaned_data.get('tipo')
        departamento = form.cleaned_data.get('departamento')
        estado = form.cleaned_data.get('estado')
        fecha_inicio = form.cleaned_data.get('fecha_inicio')
        fecha_fin = form.cleaned_data.get('fecha_fin')
        formato = form.cleaned_data.get('formato', 'html')

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

        # Si el formato es diferente de HTML, exportar
        if formato != 'html':
            return export_inventario(request, formato)

    # Para HTML, preparar contexto
    context = {
        'activos': activos,
        'form': form
    }

    return render(request, 'reportes/inventario_report_result.html', context)


@login_required
def inventario_categoria_report(request):
    """Reporte de inventario por categoría"""
    tipo = request.GET.get('tipo', '')

    # Filtrar activos
    activos = Activo.objects.all()

    if tipo:
        activos = activos.filter(tipo=tipo)

    # Agrupar por departamento
    por_departamento = activos.values(
        'departamento__nombre'
    ).annotate(
        total=Count('id'),
        porcentaje=Count('id') * 100.0 /
        activos.count() if activos.count() > 0 else 0
    ).order_by('-total')

    # Agrupar por estado
    por_estado = activos.values(
        'estado'
    ).annotate(
        total=Count('id'),
        porcentaje=Count('id') * 100.0 /
        activos.count() if activos.count() > 0 else 0
    ).order_by('-total')

    # Si es hardware, agrupar por marca
    por_marca = []
    if tipo == 'hardware':
        por_marca = Hardware.objects.values(
            'marca'
        ).annotate(
            total=Count('activo_id'),
            porcentaje=Count('activo_id') * 100.0 /
            Hardware.objects.count() if Hardware.objects.count() > 0 else 0
        ).order_by('-total')

    # Si es software, agrupar por tipo de licencia
    por_licencia = []
    if tipo == 'software':
        por_licencia = Software.objects.values(
            'tipo_licencia'
        ).annotate(
            total=Count('activo_id'),
            porcentaje=Count('activo_id') * 100.0 /
            Software.objects.count() if Software.objects.count() > 0 else 0
        ).order_by('-total')

    context = {
        'tipo': tipo,
        'por_departamento': por_departamento,
        'por_estado': por_estado,
        'por_marca': por_marca,
        'por_licencia': por_licencia
    }

    return render(request, 'reportes/inventario_categoria_report.html', context)


@login_required
def inventario_ubicacion_report(request):
    """Reporte de inventario por ubicación"""
    departamento_id = request.GET.get('departamento', '')

    # Filtrar activos
    activos = Activo.objects.all()

    if departamento_id:
        activos = activos.filter(departamento_id=departamento_id)

    # Agrupar por ubicación
    total_activos = activos.count()
    por_ubicacion = activos.values(
        'ubicacion'
    ).annotate(
        total=Count('id'),
        porcentaje=Count('id') * 100.0 /
        total_activos if total_activos > 0 else 0
    ).order_by('-total')

    # Agrupar por tipo
    por_tipo = activos.values(
        'tipo'
    ).annotate(
        total=Count('id'),
        porcentaje=Count('id') * 100.0 /
        total_activos if total_activos > 0 else 0
    ).order_by('-total')

    # Agrupar por estado
    por_estado = activos.values(
        'estado'
    ).annotate(
        total=Count('id'),
        porcentaje=Count('id') * 100.0 /
        total_activos if total_activos > 0 else 0
    ).order_by('-total')

    # Departamentos para el dropdown
    departamentos = Departamento.objects.all()

    context = {
        'departamento_id': departamento_id,
        'departamentos': departamentos,
        'por_ubicacion': por_ubicacion,
        'por_tipo': por_tipo,
        'por_estado': por_estado
    }

    return render(request, 'reportes/inventario_ubicacion_report.html', context)


@login_required
def obsolescencia_report(request):
    """Reporte de activos obsoletos o próximos a serlo"""
    # Activos marcados como obsoletos
    activos_obsoletos = Activo.objects.filter(
        estado='obsoleto').select_related('departamento')

    # Hardware con garantía vencida
    hoy = timezone.now().date()
    hardware_garantia_vencida = Hardware.objects.filter(
        fecha_garantia__lt=hoy
    ).select_related('activo')

    # Añadir días vencido
    for hardware in hardware_garantia_vencida:
        hardware.dias_vencido = (hoy - hardware.fecha_garantia).days

    # Software con licencia vencida
    software_licencia_vencida = Software.objects.filter(
        fecha_vencimiento__lt=hoy
    ).select_related('activo')

    # Añadir días vencido
    for software in software_licencia_vencida:
        software.dias_vencido = (hoy - software.fecha_vencimiento).days

    context = {
        'activos_obsoletos': activos_obsoletos,
        'hardware_garantia_vencida': hardware_garantia_vencida,
        'software_licencia_vencida': software_licencia_vencida
    }

    return render(request, 'reportes/obsolencia_report.html', context)


@login_required
def mantenimiento_report(request):
    """Página para generar reporte de mantenimientos"""
    from .forms import MantenimientoReportForm

    if request.method == 'GET' and any(param for param in request.GET if param not in ['page']):
        # Si hay parámetros en la URL, procesar el formulario
        form = MantenimientoReportForm(request.GET)
        if form.is_valid():
            # Exportar directamente en el formato seleccionado
            formato = form.cleaned_data.get('formato', 'pdf')
            return export_mantenimiento(request, format=formato)
    else:
        # Si no hay parámetros, mostrar formulario vacío
        form = MantenimientoReportForm()

    context = {
        'form': form
    }

    return render(request, 'reportes/mantenimiento_report.html', context)


@login_required
def mantenimiento_report_result(request):
    """Resultados del reporte de mantenimientos"""
    from .forms import MantenimientoReportForm

    # Obtener parámetros del formulario
    form = MantenimientoReportForm(request.GET)

    # Filtrar mantenimientos
    mantenimientos = Mantenimiento.objects.all().select_related('activo', 'responsable')

    if form.is_valid():
        tipo = form.cleaned_data.get('tipo')
        estado = form.cleaned_data.get('estado')
        responsable = form.cleaned_data.get('responsable')
        fecha_inicio = form.cleaned_data.get('fecha_inicio')
        fecha_fin = form.cleaned_data.get('fecha_fin')
        formato = form.cleaned_data.get('formato', 'html')

        if tipo:
            mantenimientos = mantenimientos.filter(tipo=tipo)

        if estado:
            mantenimientos = mantenimientos.filter(estado=estado)

        if responsable:
            mantenimientos = mantenimientos.filter(responsable=responsable)

        if fecha_inicio:
            mantenimientos = mantenimientos.filter(
                fecha_programada__gte=fecha_inicio)

        if fecha_fin:
            mantenimientos = mantenimientos.filter(
                fecha_programada__lte=fecha_fin)

        # Si el formato es diferente de HTML, exportar
        if formato != 'html':
            return export_mantenimiento(request, formato)

    # Calcular estadísticas
    completados = mantenimientos.filter(estado='completado').count()
    pendientes = mantenimientos.filter(
        Q(estado='programado') | Q(estado='en_proceso')).count()

    # Calcular costo total
    costo_total = mantenimientos.aggregate(total=Sum('costo'))['total'] or 0

    context = {
        'mantenimientos': mantenimientos,
        'completados': completados,
        'pendientes': pendientes,
        'costo_total': costo_total,
        'form': form
    }

    return render(request, 'reportes/mantenimiento_report_result.html', context)


@login_required
def transformacion_digital_report(request):
    """Página para generar reporte de transformación digital"""
    from .forms import TransformacionDigitalReportForm

    if request.method == 'GET' and any(param for param in request.GET if param not in ['page']):
        # Si hay parámetros en la URL, procesar el formulario
        form = TransformacionDigitalReportForm(request.GET)
        if form.is_valid():
            # Exportar directamente en el formato seleccionado
            formato = form.cleaned_data.get('formato', 'pdf')
            return export_diagnostico(request, format=formato)
    else:
        # Si no hay parámetros, mostrar formulario vacío
        form = TransformacionDigitalReportForm()

    context = {
        'form': form
    }

    return render(request, 'reportes/transformacion_digital_report.html', context)


@login_required
def transformacion_digital_report_result(request):
    """Resultados del reporte de transformación digital"""
    try:
        # Importar modelos de diagnóstico
        from .forms import TransformacionDigitalReportForm
        from diagnostico.models import Diagnostico, Indicador

        # Obtener parámetros del formulario
        form = TransformacionDigitalReportForm(request.GET)

        # Filtrar diagnósticos
        diagnosticos = Diagnostico.objects.all().select_related(
            'departamento', 'cuestionario', 'responsable')

        if form.is_valid():
            departamento = form.cleaned_data.get('departamento')
            fecha_inicio = form.cleaned_data.get('fecha_inicio')
            fecha_fin = form.cleaned_data.get('fecha_fin')
            formato = form.cleaned_data.get('formato', 'html')

            if departamento:
                diagnosticos = diagnosticos.filter(departamento=departamento)

            if fecha_inicio:
                diagnosticos = diagnosticos.filter(fecha__gte=fecha_inicio)

            if fecha_fin:
                diagnosticos = diagnosticos.filter(fecha__lte=fecha_fin)

            # Si el formato es diferente de HTML, exportar
            if formato != 'html':
                return export_diagnostico(request, formato)

        # Calcular nivel general
        nivel_general = diagnosticos.aggregate(Avg('nivel_general'))[
            'nivel_general__avg'] or 0

        # Obtener indicadores por departamento
        indicadores_por_departamento = []
        for diag in diagnosticos:
            indicadores = Indicador.objects.filter(diagnostico=diag)
            if indicadores.exists():
                nivel_dept = indicadores.aggregate(
                    nivel=Avg('valor'))['nivel'] or 0
                indicadores_por_departamento.append({
                    'departamento': diag.departamento.nombre,
                    'nivel': nivel_dept
                })

        context = {
            'diagnosticos': diagnosticos,
            'nivel_general': nivel_general,
            'indicadores_por_departamento': indicadores_por_departamento,
            'form': form
        }

        return render(request, 'reportes/transformacion_digital_report_result.html', context)

    except ImportError:
        # Si no existe el módulo de diagnóstico
        return render(request, 'reportes/transformacion_digital_report.html', {
            'error': 'El módulo de diagnóstico no está disponible.'
        })


# Funciones de exportación
@login_required
def export_inventario(request, format):
    """Exportar reporte de inventario a PDF o Excel"""
    # Obtener los mismos filtros que se usaron en el reporte
    tipo = request.GET.get('tipo', '')
    departamento = request.GET.get('departamento', '')
    estado = request.GET.get('estado', '')
    fecha_inicio = request.GET.get('fecha_inicio', '')
    fecha_fin = request.GET.get('fecha_fin', '')

    # Filtrar activos
    activos = Activo.objects.all().select_related('departamento')

    if tipo:
        activos = activos.filter(tipo=tipo)

    if departamento:
        activos = activos.filter(departamento_id=departamento)

    if estado:
        activos = activos.filter(estado=estado)

    if fecha_inicio:
        activos = activos.filter(fecha_adquisicion__gte=fecha_inicio)

    if fecha_fin:
        activos = activos.filter(fecha_adquisicion__lte=fecha_fin)

    if format == 'excel' and xlsxwriter:
        # Crear respuesta Excel
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet()

        # Formato para encabezados
        header_format = workbook.add_format(
            {'bold': True, 'bg_color': '#4e73df', 'color': 'white'})

        # Escribir encabezados
        headers = ['ID', 'Nombre', 'Tipo', 'Departamento',
                   'Estado', 'Valor', 'Fecha Adquisición']
        for col_num, header in enumerate(headers):
            worksheet.write(0, col_num, header, header_format)

        # Escribir datos
        for row_num, activo in enumerate(activos, 1):
            worksheet.write(row_num, 0, activo.id)
            worksheet.write(row_num, 1, activo.nombre)
            worksheet.write(row_num, 2, activo.get_tipo_display())
            worksheet.write(row_num, 3, activo.departamento.nombre)
            worksheet.write(row_num, 4, activo.get_estado_display())
            worksheet.write(row_num, 5, float(activo.valor_adquisicion))
            worksheet.write(
                row_num, 6, activo.fecha_adquisicion.strftime('%Y-%m-%d'))

        workbook.close()
        output.seek(0)

        response = HttpResponse(
            output.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename="inventario.xlsx"'
        return response

    elif format == 'pdf':
        # Crear respuesta PDF
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="inventario.pdf"'

        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(letter),
                                rightMargin=72, leftMargin=72,
                                topMargin=72, bottomMargin=72)
        elements = []

        # Estilos
        styles = getSampleStyleSheet()
        title_style = styles['Heading1']
        subtitle_style = styles['Heading2']
        normal_style = styles['Normal']

        # Título y subtítulo
        elements.append(Paragraph("Reporte de Inventario", title_style))
        elements.append(Spacer(1, 12))

        # Filtros aplicados
        filtros = []
        if tipo:
            filtros.append(f"Tipo: {tipo}")
        if departamento:
            dept_name = Departamento.objects.filter(id=departamento).first()
            if dept_name:
                filtros.append(f"Departamento: {dept_name.nombre}")
        if estado:
            estado_display = dict(Activo.ESTADO_CHOICES).get(estado, estado)
            filtros.append(f"Estado: {estado_display}")
        if fecha_inicio:
            filtros.append(f"Desde: {fecha_inicio}")
        if fecha_fin:
            filtros.append(f"Hasta: {fecha_fin}")

        if filtros:
            elements.append(Paragraph("Filtros aplicados: " +
                            ", ".join(filtros), normal_style))
            elements.append(Spacer(1, 12))

        # Datos para la tabla
        data = [['ID', 'Nombre', 'Tipo', 'Departamento', 'Estado', 'Valor', 'Fecha']]

        for activo in activos:
            data.append([
                str(activo.id),
                activo.nombre,
                activo.get_tipo_display(),
                activo.departamento.nombre,
                activo.get_estado_display(),
                f"${activo.valor_adquisicion}",
                activo.fecha_adquisicion.strftime('%Y-%m-%d')
            ])

        # Crear tabla
        table = Table(data, repeatRows=1)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.blue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))

        elements.append(table)

        # Resumen
        elements.append(Spacer(1, 20))
        elements.append(Paragraph("Resumen", subtitle_style))
        elements.append(Spacer(1, 6))

        total_activos = len(activos)
        valor_total = sum(float(activo.valor_adquisicion)
                          for activo in activos)
        valor_promedio = valor_total / total_activos if total_activos > 0 else 0

        elements.append(
            Paragraph(f"Total de activos: {total_activos}", normal_style))
        elements.append(
            Paragraph(f"Valor total: ${valor_total:.2f}", normal_style))
        elements.append(
            Paragraph(f"Valor promedio: ${valor_promedio:.2f}", normal_style))

        # Construir PDF
        doc.build(elements)
        pdf = buffer.getvalue()
        buffer.close()

        response.write(pdf)
        return response

    else:
        # Por defecto, exportar como PDF si no se especifica o no es válido
        return export_inventario(request, 'pdf')


@login_required
def export_mantenimiento(request, format):
    """Exportar reporte de mantenimientos a PDF o Excel"""
    # Obtener los mismos filtros que se usaron en el reporte
    tipo = request.GET.get('tipo', '')
    estado = request.GET.get('estado', '')
    responsable = request.GET.get('responsable', '')
    fecha_inicio = request.GET.get('fecha_inicio', '')
    fecha_fin = request.GET.get('fecha_fin', '')

    # Filtrar mantenimientos
    mantenimientos = Mantenimiento.objects.all().select_related('activo', 'responsable')

    if tipo:
        mantenimientos = mantenimientos.filter(tipo=tipo)

    if estado:
        mantenimientos = mantenimientos.filter(estado=estado)

    if responsable:
        mantenimientos = mantenimientos.filter(responsable_id=responsable)

    if fecha_inicio:
        mantenimientos = mantenimientos.filter(
            fecha_programada__gte=fecha_inicio)

    if fecha_fin:
        mantenimientos = mantenimientos.filter(fecha_programada__lte=fecha_fin)

    if format == 'excel' and xlsxwriter:
        # Crear respuesta Excel
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet()

        # Formato para encabezados
        header_format = workbook.add_format(
            {'bold': True, 'bg_color': '#4e73df', 'color': 'white'})

        # Escribir encabezados
        headers = ['ID', 'Activo', 'Tipo', 'Fecha Programada',
                   'Fecha Realización', 'Responsable', 'Estado', 'Costo']
        for col_num, header in enumerate(headers):
            worksheet.write(0, col_num, header, header_format)

        # Escribir datos
        for row_num, mant in enumerate(mantenimientos, 1):
            worksheet.write(row_num, 0, mant.id)
            worksheet.write(row_num, 1, mant.activo.nombre)
            worksheet.write(row_num, 2, mant.get_tipo_display())
            worksheet.write(
                row_num, 3, mant.fecha_programada.strftime('%Y-%m-%d'))
            worksheet.write(row_num, 4, mant.fecha_realizacion.strftime(
                '%Y-%m-%d') if mant.fecha_realizacion else 'Pendiente')
            worksheet.write(
                row_num, 5, mant.responsable.get_full_name() if mant.responsable else '')
            worksheet.write(row_num, 6, mant.get_estado_display())
            worksheet.write(row_num, 7, float(
                mant.costo) if mant.costo else 0.0)

        workbook.close()
        output.seek(0)

        response = HttpResponse(
            output.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename="mantenimientos.xlsx"'
        return response

    elif format == 'pdf':
        # Crear respuesta PDF
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="mantenimientos.pdf"'

        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(letter),
                                rightMargin=72, leftMargin=72,
                                topMargin=72, bottomMargin=72)
        elements = []

        # Estilos
        styles = getSampleStyleSheet()
        title_style = styles['Heading1']
        subtitle_style = styles['Heading2']
        normal_style = styles['Normal']

        # Título
        elements.append(Paragraph("Reporte de Mantenimientos", title_style))
        elements.append(Spacer(1, 12))

        # Filtros aplicados
        filtros = []
        if tipo:
            tipo_display = dict(Mantenimiento.TIPO_CHOICES).get(tipo, tipo)
            filtros.append(f"Tipo: {tipo_display}")
        if estado:
            estado_display = dict(
                Mantenimiento.ESTADO_CHOICES).get(estado, estado)
            filtros.append(f"Estado: {estado_display}")
        if responsable:
            resp_name = User.objects.filter(id=responsable).first()
            if resp_name:
                filtros.append(
                    f"Responsable: {resp_name.get_full_name() or resp_name.username}")
        if fecha_inicio:
            filtros.append(f"Desde: {fecha_inicio}")
        if fecha_fin:
            filtros.append(f"Hasta: {fecha_fin}")

        if filtros:
            elements.append(Paragraph("Filtros aplicados: " +
                            ", ".join(filtros), normal_style))
            elements.append(Spacer(1, 12))

        # Datos para la tabla
        data = [['ID', 'Activo', 'Tipo', 'Fecha Prog.',
                 'Fecha Real.', 'Responsable', 'Estado', 'Costo']]

        for mant in mantenimientos:
            data.append([
                str(mant.id),
                mant.activo.nombre,
                mant.get_tipo_display(),
                mant.fecha_programada.strftime('%Y-%m-%d'),
                mant.fecha_realizacion.strftime(
                    '%Y-%m-%d') if mant.fecha_realizacion else 'Pendiente',
                mant.responsable.get_full_name() if mant.responsable else '',
                mant.get_estado_display(),
                f"${mant.costo}" if mant.costo else "No especificado"
            ])

        # Crear tabla
        table = Table(data, repeatRows=1)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.blue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))

        elements.append(table)

        # Resumen
        elements.append(Spacer(1, 20))
        elements.append(Paragraph("Resumen", subtitle_style))
        elements.append(Spacer(1, 6))

        # Calcular estadísticas
        completados = mantenimientos.filter(estado='completado').count()
        pendientes = mantenimientos.filter(
            Q(estado='programado') | Q(estado='en_proceso')).count()
        costo_total = mantenimientos.aggregate(
            total=Sum('costo'))['total'] or 0

        elements.append(
            Paragraph(f"Total de mantenimientos: {mantenimientos.count()}", normal_style))
        elements.append(Paragraph(f"Completados: {completados}", normal_style))
        elements.append(Paragraph(f"Pendientes: {pendientes}", normal_style))
        elements.append(
            Paragraph(f"Costo total: ${costo_total:.2f}", normal_style))

        # Construir PDF
        doc.build(elements)
        pdf = buffer.getvalue()
        buffer.close()

        response.write(pdf)
        return response

    else:
        # Por defecto, exportar como PDF
        return export_mantenimiento(request, 'pdf')


@login_required
def export_diagnostico(request, format):
    """Exportar reporte de diagnóstico a PDF o Excel"""
    try:
        from diagnostico.models import Diagnostico, Indicador

        # Obtener los mismos filtros que se usaron en el reporte
        departamento = request.GET.get('departamento', '')
        fecha_inicio = request.GET.get('fecha_inicio', '')
        fecha_fin = request.GET.get('fecha_fin', '')

        # Filtrar diagnósticos
        diagnosticos = Diagnostico.objects.all().select_related(
            'departamento', 'cuestionario', 'responsable')

        if departamento:
            diagnosticos = diagnosticos.filter(departamento_id=departamento)

        if fecha_inicio:
            diagnosticos = diagnosticos.filter(fecha__gte=fecha_inicio)

        if fecha_fin:
            diagnosticos = diagnosticos.filter(fecha__lte=fecha_fin)

        if format == 'excel' and xlsxwriter:
            # Crear respuesta Excel
            output = BytesIO()
            workbook = xlsxwriter.Workbook(output)
            worksheet = workbook.add_worksheet('Diagnósticos')

            # Formato para encabezados
            header_format = workbook.add_format(
                {'bold': True, 'bg_color': '#4e73df', 'color': 'white'})

            # Escribir encabezados
            headers = ['ID', 'Departamento', 'Cuestionario', 'Fecha',
                       'Responsable', 'Nivel General']
            for col_num, header in enumerate(headers):
                worksheet.write(0, col_num, header, header_format)

            # Escribir datos de diagnósticos
            for row_num, diag in enumerate(diagnosticos, 1):
                worksheet.write(row_num, 0, diag.id)
                worksheet.write(row_num, 1, diag.departamento.nombre)
                worksheet.write(row_num, 2, diag.cuestionario.titulo)
                worksheet.write(
                    row_num, 3, diag.fecha.strftime('%Y-%m-%d %H:%M'))
                worksheet.write(
                    row_num, 4, diag.responsable.get_full_name() if diag.responsable else '')
                worksheet.write(row_num, 5, float(
                    diag.nivel_general) if diag.nivel_general else 0)

            # Crear hoja para indicadores
            if diagnosticos.exists():
                worksheet_ind = workbook.add_worksheet('Indicadores')

                # Encabezados para indicadores
                ind_headers = ['Departamento', 'Diagnóstico ID',
                               'Nombre', 'Valor', 'Descripción']
                for col_num, header in enumerate(ind_headers):
                    worksheet_ind.write(0, col_num, header, header_format)

                # Obtener indicadores
                row_num = 1
                for diag in diagnosticos:
                    indicadores = Indicador.objects.filter(diagnostico=diag)
                    for ind in indicadores:
                        worksheet_ind.write(
                            row_num, 0, diag.departamento.nombre)
                        worksheet_ind.write(row_num, 1, diag.id)
                        worksheet_ind.write(row_num, 2, ind.nombre)
                        worksheet_ind.write(row_num, 3, float(
                            ind.valor) if ind.valor else 0)
                        worksheet_ind.write(row_num, 4, ind.descripcion or '')
                        row_num += 1

            workbook.close()
            output.seek(0)

            response = HttpResponse(
                output.read(),
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = 'attachment; filename="diagnostico.xlsx"'
            return response

        elif format == 'pdf':
            # Crear respuesta PDF
            response = HttpResponse(content_type='application/pdf')
            response['Content-Disposition'] = 'attachment; filename="diagnostico.pdf"'

            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            elements = []

            # Estilos
            styles = getSampleStyleSheet()
            title_style = styles['Heading1']
            subtitle_style = styles['Heading2']
            normal_style = styles['Normal']

            # Título
            elements.append(
                Paragraph("Reporte de Transformación Digital", title_style))
            elements.append(Spacer(1, 12))

            # Filtros aplicados
            filtros = []
            if departamento:
                dept_name = Departamento.objects.filter(
                    id=departamento).first()
                if dept_name:
                    filtros.append(f"Departamento: {dept_name.nombre}")
            if fecha_inicio:
                filtros.append(f"Desde: {fecha_inicio}")
            if fecha_fin:
                filtros.append(f"Hasta: {fecha_fin}")

            if filtros:
                elements.append(
                    Paragraph("Filtros aplicados: " + ", ".join(filtros), normal_style))
                elements.append(Spacer(1, 12))

            # Calcular nivel general
            nivel_general = diagnosticos.aggregate(Avg('nivel_general'))[
                'nivel_general__avg'] or 0

            elements.append(Paragraph(
                f"Nivel General de Transformación Digital: {nivel_general:.2f}/5", subtitle_style))
            elements.append(Spacer(1, 12))

            # Datos para la tabla de diagnósticos
            elements.append(Paragraph("Diagnósticos", subtitle_style))
            elements.append(Spacer(1, 6))

            data = [['ID', 'Departamento', 'Cuestionario', 'Fecha', 'Nivel']]

            for diag in diagnosticos:
                data.append([
                    str(diag.id),
                    diag.departamento.nombre,
                    diag.cuestionario.titulo,
                    diag.fecha.strftime('%Y-%m-%d'),
                    str(diag.nivel_general or 0)
                ])

            # Crear tabla
            table = Table(data, repeatRows=1)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.blue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))

            elements.append(table)
            elements.append(Spacer(1, 12))

            # Recomendaciones basadas en el nivel
            elements.append(Paragraph("Recomendaciones", subtitle_style))
            elements.append(Spacer(1, 6))

            if nivel_general < 2:
                elements.append(Paragraph(
                    "La institución se encuentra en un nivel básico de transformación digital. Es necesario implementar acciones inmediatas para mejorar.", normal_style))
                elements.append(Paragraph(
                    "• Desarrollar un plan estratégico de transformación digital", normal_style))
                elements.append(
                    Paragraph("• Actualizar la infraestructura tecnológica básica", normal_style))
                elements.append(Paragraph(
                    "• Capacitar al personal en competencias digitales básicas", normal_style))
            elif nivel_general < 3:
                elements.append(Paragraph(
                    "La institución se encuentra en un nivel medio-bajo de transformación digital. Se requiere mayor avance.", normal_style))
                elements.append(Paragraph(
                    "• Fortalecer la infraestructura tecnológica existente", normal_style))
                elements.append(
                    Paragraph("• Digitalizar procesos administrativos clave", normal_style))
                elements.append(Paragraph(
                    "• Desarrollar políticas de gestión de datos institucionales", normal_style))
            elif nivel_general < 4:
                elements.append(Paragraph(
                    "La institución se encuentra en un nivel medio-alto de transformación digital. Se pueden optimizar algunos procesos.", normal_style))
                elements.append(
                    Paragraph("• Integrar los sistemas digitales existentes", normal_style))
                elements.append(
                    Paragraph("• Implementar soluciones de analítica avanzada", normal_style))
                elements.append(
                    Paragraph("• Optimizar la experiencia digital del estudiante", normal_style))
            else:
                elements.append(Paragraph(
                    "La institución se encuentra en un nivel alto de transformación digital. Se recomienda mantenimiento y mejora continua.", normal_style))
                elements.append(Paragraph(
                    "• Mantener actualizadas las tecnologías implementadas", normal_style))
                elements.append(Paragraph(
                    "• Compartir buenas prácticas con otras instituciones", normal_style))
                elements.append(
                    Paragraph("• Reforzar las políticas de ciberseguridad", normal_style))

            # Construir PDF
            doc.build(elements)
            pdf = buffer.getvalue()
            buffer.close()

            response.write(pdf)
            return response

        else:
            # Por defecto, exportar como PDF
            return export_diagnostico(request, 'pdf')

    except ImportError:
        # Si no existe el módulo de diagnóstico
        return redirect('transformacion_digital_report')
