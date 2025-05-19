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

# Importaciones de modelos
from inventario.models import Activo, Hardware, Software, Mantenimiento, Proveedor
from locales.models import Local, Equipamiento
from usuarios.models import Departamento
from diagnostico.models import Diagnostico, Indicador

# Librerías para exportación
try:
    import xlsxwriter
except ImportError:
    xlsxwriter = None

try:
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Image, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
except ImportError:
    reportlab = None


@login_required
def index(request):
    """Vista principal del módulo de reportes"""
    return render(request, 'reportes/index.html')


@login_required
def reportes_dashboard(request):
    """Dashboard principal con indicadores clave"""
    # Datos para el dashboard
    total_activos = Activo.objects.count()
    total_hardware = Hardware.objects.count()
    total_software = Software.objects.count()

    # Mantenimientos pendientes
    mantenimientos_pendientes = Mantenimiento.objects.filter(
        Q(estado='programado') | Q(estado='en_proceso')
    ).count()

    # Activos por departamento
    activos_por_departamento = Activo.objects.values(
        'departamento__nombre'
    ).annotate(
        total=Count('id'),
        porcentaje=Count('id') * 100.0 / total_activos
    ).order_by('-total')

    # Activos por estado
    activos_por_estado = Activo.objects.values(
        'estado'
    ).annotate(
        total=Count('id'),
        porcentaje=Count('id') * 100.0 / total_activos
    ).order_by('-total')

    # Software por vencer (próximos 30 días)
    hoy = timezone.now().date()
    treinta_dias = hoy + timedelta(days=30)
    software_por_vencer = Software.objects.filter(
        fecha_vencimiento__isnull=False,
        fecha_vencimiento__gte=hoy,
        fecha_vencimiento__lte=treinta_dias
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
        'nivel_transformacion': nivel_transformacion
    }

    return render(request, 'reportes/dashboard.html', context)


@login_required
def inventario_report(request):
    """Página para generar reporte de inventario"""
    # Datos para el formulario
    departamentos = Departamento.objects.all()

    context = {
        'departamentos': departamentos,
        'form': {
            'fields': {
                'departamento': {
                    'queryset': departamentos
                }
            }
        }
    }

    return render(request, 'reportes/inventario_report.html', context)


@login_required
def inventario_report_result(request):
    """Resultados del reporte de inventario"""
    # Obtener parámetros del formulario
    tipo = request.GET.get('tipo', '')
    departamento = request.GET.get('departamento', '')
    estado = request.GET.get('estado', '')
    fecha_inicio = request.GET.get('fecha_inicio', '')
    fecha_fin = request.GET.get('fecha_fin', '')
    formato = request.GET.get('formato', 'html')

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

    # Si el formato es diferente de HTML, exportar
    if formato != 'html':
        return export_inventario(request, activos, formato)

    # Para HTML, preparar contexto
    departamentos = Departamento.objects.all()

    context = {
        'activos': activos,
        'form': {
            'tipo': {'value': tipo},
            'departamento': {'value': departamento},
            'estado': {'value': estado},
            'fecha_inicio': {'value': fecha_inicio},
            'fecha_fin': {'value': fecha_fin},
            'formato': {'value': formato},
            'fields': {
                'departamento': {
                    'queryset': departamentos
                }
            }
        }
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
    # Datos para el formulario
    from django.contrib.auth.models import User
    usuarios = User.objects.all()

    context = {
        'form': {
            'fields': {
                'responsable': {
                    'queryset': usuarios
                }
            }
        }
    }

    return render(request, 'reportes/mantenimiento_report.html', context)


@login_required
def mantenimiento_report_result(request):
    """Resultados del reporte de mantenimientos"""
    # Obtener parámetros del formulario
    tipo = request.GET.get('tipo', '')
    estado = request.GET.get('estado', '')
    responsable = request.GET.get('responsable', '')
    fecha_inicio = request.GET.get('fecha_inicio', '')
    fecha_fin = request.GET.get('fecha_fin', '')
    formato = request.GET.get('formato', 'html')

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

    # Si el formato es diferente de HTML, exportar
    if formato != 'html':
        return export_mantenimiento(request, mantenimientos, formato)

    # Calcular estadísticas
    completados = mantenimientos.filter(estado='completado').count()
    pendientes = mantenimientos.filter(
        Q(estado='programado') | Q(estado='en_proceso')).count()

    # Calcular costo total
    from django.db.models import Sum
    costo_total = mantenimientos.aggregate(total=Sum('costo'))['total'] or 0

    # Para HTML, preparar contexto
    from django.contrib.auth.models import User
    usuarios = User.objects.all()

    context = {
        'mantenimientos': mantenimientos,
        'completados': completados,
        'pendientes': pendientes,
        'costo_total': costo_total,
        'form': {
            'tipo': {'value': tipo},
            'estado': {'value': estado},
            'responsable': {'value': responsable},
            'fecha_inicio': {'value': fecha_inicio},
            'fecha_fin': {'value': fecha_fin},
            'formato': {'value': formato},
            'fields': {
                'responsable': {
                    'queryset': usuarios
                }
            }
        }
    }

    return render(request, 'reportes/mantenimiento_report_result.html', context)


@login_required
def transformacion_digital_report(request):
    """Página para generar reporte de transformación digital"""
    departamentos = Departamento.objects.all()

    context = {
        'form': {
            'fields': {
                'departamento': {
                    'queryset': departamentos
                }
            }
        }
    }

    return render(request, 'reportes/transformacion_digital_report.html', context)


@login_required
def transformacion_digital_report_result(request):
    """Resultados del reporte de transformación digital"""
    try:
        # Importar modelos de diagnóstico
        from diagnostico.models import Diagnostico, Indicador

        # Obtener parámetros del formulario
        departamento = request.GET.get('departamento', '')
        fecha_inicio = request.GET.get('fecha_inicio', '')
        fecha_fin = request.GET.get('fecha_fin', '')
        formato = request.GET.get('formato', 'html')

        # Filtrar diagnósticos
        diagnosticos = Diagnostico.objects.all().select_related(
            'departamento', 'cuestionario', 'responsable')

        if departamento:
            diagnosticos = diagnosticos.filter(departamento_id=departamento)

        if fecha_inicio:
            diagnosticos = diagnosticos.filter(fecha__gte=fecha_inicio)

        if fecha_fin:
            diagnosticos = diagnosticos.filter(fecha__lte=fecha_fin)

        # Si el formato es diferente de HTML, exportar
        if formato != 'html':
            return export_diagnostico(request, diagnosticos, formato)

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

        # Para HTML, preparar contexto
        departamentos = Departamento.objects.all()

        context = {
            'diagnosticos': diagnosticos,
            'nivel_general': nivel_general,
            'indicadores_por_departamento': indicadores_por_departamento,
            'form': {
                'departamento': {'value': departamento},
                'fecha_inicio': {'value': fecha_inicio},
                'fecha_fin': {'value': fecha_fin},
                'formato': {'value': formato},
                'fields': {
                    'departamento': {
                        'queryset': departamentos
                    }
                }
            }
        }

        return render(request, 'reportes/transformacion_digital_report_result.html', context)

    except ImportError:
        # Si no existe el módulo de diagnóstico
        return render(request, 'reportes/transformacion_digital_report.html', {
            'error': 'El módulo de diagnóstico no está disponible.'
        })


# Funciones de exportación

def export_inventario(request, activos, formato):
    """Exportar reporte de inventario a diferentes formatos"""
    if formato == 'csv':
        # Crear respuesta CSV
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="inventario.csv"'

        writer = csv.writer(response)
        writer.writerow(['ID', 'Nombre', 'Tipo', 'Departamento',
                        'Estado', 'Valor', 'Fecha Adquisición'])

        for activo in activos:
            writer.writerow([
                activo.id,
                activo.nombre,
                activo.get_tipo_display(),
                activo.departamento.nombre,
                activo.get_estado_display(),
                activo.valor_adquisicion,
                activo.fecha_adquisicion
            ])

        return response

    elif formato == 'excel' and xlsxwriter:
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

    elif formato == 'pdf' and reportlab:
        # Crear respuesta PDF
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="inventario.pdf"'

        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []

        # Estilos
        styles = getSampleStyleSheet()
        title_style = styles['Heading1']

        # Título
        elements.append(Paragraph("Reporte de Inventario", title_style))
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
                str(activo.valor_adquisicion),
                activo.fecha_adquisicion.strftime('%Y-%m-%d')
            ])

        # Crear tabla
        table = Table(data)
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

        # Construir PDF
        doc.build(elements)
        pdf = buffer.getvalue()
        buffer.close()

        response.write(pdf)
        return response

    else:
        # Si no se pudo exportar, redirigir al reporte HTML
        return redirect('inventario_report_result')


def export_mantenimiento(request, mantenimientos, formato):
    """Exportar reporte de mantenimientos a diferentes formatos"""
    if formato == 'csv':
        # Crear respuesta CSV
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="mantenimientos.csv"'

        writer = csv.writer(response)
        writer.writerow(['ID', 'Activo', 'Tipo', 'Fecha Programada',
                        'Fecha Realización', 'Responsable', 'Estado', 'Costo'])

        for mant in mantenimientos:
            writer.writerow([
                mant.id,
                mant.activo.nombre,
                mant.get_tipo_display(),
                mant.fecha_programada,
                mant.fecha_realizacion or '',
                mant.responsable.get_full_name() if mant.responsable else '',
                mant.get_estado_display(),
                mant.costo or ''
            ])

        return response

    elif formato == 'excel' and xlsxwriter:
        # Implementación similar a export_inventario pero para mantenimientos
        # ...
        return HttpResponse("Exportación a Excel no implementada")

    elif formato == 'pdf' and reportlab:
        # Implementación similar a export_inventario pero para mantenimientos
        # ...
        return HttpResponse("Exportación a PDF no implementada")

    else:
        # Si no se pudo exportar, redirigir al reporte HTML
        return redirect('mantenimiento_report_result')


def export_diagnostico(request, diagnosticos, formato):
    """Exportar reporte de diagnóstico a diferentes formatos"""
    # Implementación similar a export_inventario pero para diagnósticos
    # ...
    return HttpResponse(f"Exportación a {formato} no implementada")
