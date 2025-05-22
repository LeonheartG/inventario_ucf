# reportes/utils.py
import os
import json
from io import BytesIO
from datetime import datetime
from django.http import HttpResponse
from django.conf import settings
from django.template.loader import get_template
from django.template import Context
import base64

# Importaciones condicionales para PDF
try:
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Image, Spacer, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, landscape, A4
    from reportlab.lib.units import inch, cm
    from reportlab.lib.utils import ImageReader
    from reportlab.graphics.shapes import Drawing
    from reportlab.graphics.charts.piecharts import Pie
    from reportlab.graphics.charts.barcharts import VerticalBarChart
    from reportlab.graphics.charts.linecharts import HorizontalLineChart
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

# Importaciones condicionales para Excel
try:
    import xlsxwriter
    from xlsxwriter.utility import xl_rowcol_to_cell
    XLSXWRITER_AVAILABLE = True
except ImportError:
    XLSXWRITER_AVAILABLE = False

# Importaciones para gráficos
try:
    import matplotlib
    matplotlib.use('Agg')  # Use non-interactive backend
    import matplotlib.pyplot as plt
    import seaborn as sns
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False


class ExportManager:
    """Clase principal para manejar exportaciones"""

    def __init__(self):
        self.company_name = "Universidad de Cienfuegos"
        self.company_logo = None
        self.setup_logo()

    def setup_logo(self):
        """Configurar logo de la empresa"""
        logo_path = os.path.join(
            settings.STATIC_ROOT or settings.STATICFILES_DIRS[0], 'img', 'logo_ucf.png')
        if os.path.exists(logo_path):
            self.company_logo = logo_path

    def check_dependencies(self, format_type):
        """Verificar dependencias necesarias"""
        if format_type.lower() == 'pdf' and not REPORTLAB_AVAILABLE:
            raise ImportError(
                "ReportLab no está instalado. Ejecute: pip install reportlab")
        elif format_type.lower() == 'excel' and not XLSXWRITER_AVAILABLE:
            raise ImportError(
                "XlsxWriter no está instalado. Ejecute: pip install xlsxwriter")

    def create_pdf_response(self, filename):
        """Crear respuesta HTTP para PDF"""
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

    def create_excel_response(self, filename):
        """Crear respuesta HTTP para Excel"""
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response


class PDFExporter(ExportManager):
    """Exportador especializado en PDF"""

    def __init__(self):
        super().__init__()
        if not REPORTLAB_AVAILABLE:
            raise ImportError("ReportLab no está disponible")

        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()

    def setup_custom_styles(self):
        """Configurar estilos personalizados"""
        # Estilo para título principal
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#006699'),
            fontName='Helvetica-Bold'
        ))

        # Estilo para subtítulos
        self.styles.add(ParagraphStyle(
            name='CustomSubtitle',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=15,
            textColor=colors.HexColor('#3399CC'),
            fontName='Helvetica-Bold'
        ))

        # Estilo para texto normal con mejor espaciado
        self.styles.add(ParagraphStyle(
            name='CustomNormal',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=6,
            fontName='Helvetica'
        ))

        # Estilo para texto pequeño
        self.styles.add(ParagraphStyle(
            name='CustomSmall',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=colors.grey,
            fontName='Helvetica'
        ))

    def add_header(self, elements):
        """Añadir encabezado con logo y título"""
        # Logo de la empresa
        if self.company_logo and os.path.exists(self.company_logo):
            try:
                logo = Image(self.company_logo, width=2*inch, height=0.8*inch)
                logo.hAlign = 'LEFT'
                elements.append(logo)
                elements.append(Spacer(1, 12))
            except:
                pass

        # Información de la empresa
        company_info = Paragraph(
            f"<b>{self.company_name}</b><br/>Sistema de Gestión de Inventarios Tecnológicos",
            self.styles['CustomNormal']
        )
        elements.append(company_info)
        elements.append(Spacer(1, 20))

    def add_footer_info(self, elements):
        """Añadir información del pie"""
        footer_text = f"Generado el {datetime.now().strftime('%d/%m/%Y a las %H:%M')}"
        elements.append(Spacer(1, 20))
        elements.append(Paragraph(footer_text, self.styles['CustomSmall']))

    def create_table(self, data, col_widths=None, style=None):
        """Crear tabla con estilo personalizado"""
        if not data:
            return None

        table = Table(data, colWidths=col_widths, repeatRows=1)

        # Estilo por defecto
        default_style = TableStyle([
            # Encabezado
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#006699')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),

            # Cuerpo de la tabla
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#CCCCCC')),

            # Filas alternadas
            ('ROWBACKGROUNDS', (0, 1), (-1, -1),
             [colors.white, colors.HexColor('#F8F9FA')]),

            # Padding
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ])

        if style:
            default_style.add(*style)

        table.setStyle(default_style)
        return table

    def create_chart_image(self, chart_type, data, title="", width=400, height=300):
        """Crear gráfico como imagen para incluir en PDF"""
        if not MATPLOTLIB_AVAILABLE:
            return None

        try:
            plt.style.use('seaborn-v0_8')  # Estilo moderno
            fig, ax = plt.subplots(figsize=(width/100, height/100))

            if chart_type == 'pie':
                labels = [item['label'] for item in data]
                values = [item['value'] for item in data]
                colors_list = ['#006699', '#3399CC',
                               '#48A5C6', '#66B2CC', '#84C2D1']

                wedges, texts, autotexts = ax.pie(values, labels=labels, autopct='%1.1f%%',
                                                  colors=colors_list, startangle=90)
                for autotext in autotexts:
                    autotext.set_color('white')
                    autotext.set_fontweight('bold')

            elif chart_type == 'bar':
                labels = [item['label'] for item in data]
                values = [item['value'] for item in data]
                bars = ax.bar(labels, values, color='#006699', alpha=0.7)

                # Añadir valores en las barras
                for bar in bars:
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width()/2., height,
                            f'{int(height)}', ha='center', va='bottom')

                ax.set_ylabel('Cantidad')
                plt.xticks(rotation=45, ha='right')

            elif chart_type == 'line':
                x_data = [item['x'] for item in data]
                y_data = [item['y'] for item in data]
                ax.plot(x_data, y_data, color='#006699',
                        marker='o', linewidth=2, markersize=6)
                ax.set_ylabel('Valores')
                ax.grid(True, alpha=0.3)
                plt.xticks(rotation=45, ha='right')

            ax.set_title(title, fontsize=14,
                         fontweight='bold', color='#006699')
            plt.tight_layout()

            # Guardar en memoria
            buffer = BytesIO()
            plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
            buffer.seek(0)
            plt.close()

            # Crear imagen para ReportLab
            image = Image(buffer, width=width, height=height)
            return image

        except Exception as e:
            print(f"Error creando gráfico: {e}")
            return None

    def export_data_to_pdf(self, data_config, filename):
        """Exportar datos a PDF con configuración completa"""
        response = self.create_pdf_response(filename)
        buffer = BytesIO()

        # Determinar orientación
        pagesize = landscape(letter) if data_config.get(
            'landscape', False) else letter
        doc = SimpleDocTemplate(buffer, pagesize=pagesize,
                                rightMargin=72, leftMargin=72,
                                topMargin=72, bottomMargin=72)

        elements = []

        # Encabezado
        self.add_header(elements)

        # Título del reporte
        title = data_config.get('title', 'Reporte')
        elements.append(Paragraph(title, self.styles['CustomTitle']))
        elements.append(Spacer(1, 20))

        # Filtros aplicados
        if 'filters' in data_config and data_config['filters']:
            elements.append(Paragraph("Filtros aplicados:",
                            self.styles['CustomSubtitle']))
            for filter_name, filter_value in data_config['filters'].items():
                filter_text = f"<b>{filter_name}:</b> {filter_value}"
                elements.append(
                    Paragraph(filter_text, self.styles['CustomNormal']))
            elements.append(Spacer(1, 15))

        # Resumen ejecutivo
        if 'summary' in data_config:
            elements.append(Paragraph("Resumen Ejecutivo",
                            self.styles['CustomSubtitle']))
            for key, value in data_config['summary'].items():
                summary_text = f"<b>{key}:</b> {value}"
                elements.append(
                    Paragraph(summary_text, self.styles['CustomNormal']))
            elements.append(Spacer(1, 15))

        # Gráficos
        if 'charts' in data_config:
            for chart_config in data_config['charts']:
                chart_image = self.create_chart_image(
                    chart_config['type'],
                    chart_config['data'],
                    chart_config.get('title', ''),
                    chart_config.get('width', 400),
                    chart_config.get('height', 300)
                )
                if chart_image:
                    elements.append(chart_image)
                    elements.append(Spacer(1, 20))

        # Tabla principal
        if 'table_data' in data_config and data_config['table_data']:
            table = self.create_table(
                data_config['table_data'],
                data_config.get('col_widths'),
                data_config.get('table_style')
            )
            if table:
                elements.append(table)
                elements.append(Spacer(1, 20))

        # Secciones adicionales
        if 'sections' in data_config:
            for section in data_config['sections']:
                elements.append(
                    Paragraph(section['title'], self.styles['CustomSubtitle']))
                elements.append(
                    Paragraph(section['content'], self.styles['CustomNormal']))
                elements.append(Spacer(1, 15))

        # Pie de página
        self.add_footer_info(elements)

        # Construir PDF
        doc.build(elements)
        pdf = buffer.getvalue()
        buffer.close()

        response.write(pdf)
        return response


class ExcelExporter(ExportManager):
    """Exportador especializado en Excel"""

    def __init__(self):
        super().__init__()
        if not XLSXWRITER_AVAILABLE:
            raise ImportError("XlsxWriter no está disponible")

    def create_workbook_styles(self, workbook):
        """Crear estilos para el workbook"""
        styles = {}

        # Estilo para encabezados
        styles['header'] = workbook.add_format({
            'bold': True,
            'bg_color': '#006699',
            'color': 'white',
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
            'font_size': 11
        })

        # Estilo para títulos
        styles['title'] = workbook.add_format({
            'bold': True,
            'font_size': 16,
            'color': '#006699',
            'align': 'center'
        })

        # Estilo para subtítulos
        styles['subtitle'] = workbook.add_format({
            'bold': True,
            'font_size': 12,
            'color': '#3399CC'
        })

        # Estilo para datos normales
        styles['data'] = workbook.add_format({
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
            'font_size': 10
        })

        # Estilo para números
        styles['number'] = workbook.add_format({
            'align': 'right',
            'valign': 'vcenter',
            'border': 1,
            'num_format': '#,##0.00',
            'font_size': 10
        })

        # Estilo para fechas
        styles['date'] = workbook.add_format({
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
            'num_format': 'dd/mm/yyyy',
            'font_size': 10
        })

        # Estilo para filas alternadas
        styles['data_alt'] = workbook.add_format({
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
            'bg_color': '#F8F9FA',
            'font_size': 10
        })

        # Estilo para totales
        styles['total'] = workbook.add_format({
            'bold': True,
            'bg_color': '#E6F3FF',
            'border': 1,
            'align': 'center',
            'font_size': 10
        })

        return styles

    def add_chart_to_worksheet(self, workbook, worksheet, chart_config, start_row):
        """Añadir gráfico a la hoja de trabajo"""
        try:
            chart = workbook.add_chart({'type': chart_config['type']})

            # Configurar series de datos
            for series in chart_config['series']:
                chart.add_series({
                    'categories': series.get('categories'),
                    'values': series.get('values'),
                    'name': series.get('name', ''),
                    'fill': {'color': series.get('color', '#006699')}
                })

            # Configurar título y ejes
            chart.set_title({'name': chart_config.get('title', '')})
            chart.set_x_axis({'name': chart_config.get('x_axis', '')})
            chart.set_y_axis({'name': chart_config.get('y_axis', '')})

            # Insertar gráfico
            worksheet.insert_chart(start_row, 0, chart, {
                'x_scale': chart_config.get('x_scale', 1),
                'y_scale': chart_config.get('y_scale', 1)
            })

            return start_row + 15  # Retornar nueva posición

        except Exception as e:
            print(f"Error añadiendo gráfico: {e}")
            return start_row

    def export_data_to_excel(self, data_config, filename):
        """Exportar datos a Excel con configuración completa"""
        response = self.create_excel_response(filename)
        output = BytesIO()

        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        styles = self.create_workbook_styles(workbook)

        # Hoja principal
        worksheet = workbook.add_worksheet(
            data_config.get('sheet_name', 'Datos'))

        current_row = 0

        # Título del reporte
        title = data_config.get('title', 'Reporte')
        worksheet.merge_range(current_row, 0, current_row,
                              len(data_config.get('headers', [])) - 1,
                              title, styles['title'])
        current_row += 2

        # Información general
        worksheet.write(
            current_row, 0, f"Generado el: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        current_row += 1
        worksheet.write(current_row, 0, f"Por: {self.company_name}")
        current_row += 2

        # Filtros aplicados
        if 'filters' in data_config and data_config['filters']:
            worksheet.write(
                current_row, 0, "Filtros aplicados:", styles['subtitle'])
            current_row += 1
            for filter_name, filter_value in data_config['filters'].items():
                worksheet.write(current_row, 0, f"{filter_name}:")
                worksheet.write(current_row, 1, str(filter_value))
                current_row += 1
            current_row += 1

        # Resumen ejecutivo
        if 'summary' in data_config:
            worksheet.write(
                current_row, 0, "Resumen Ejecutivo:", styles['subtitle'])
            current_row += 1
            for key, value in data_config['summary'].items():
                worksheet.write(current_row, 0, f"{key}:")
                worksheet.write(current_row, 1, value, styles['number'] if isinstance(
                    value, (int, float)) else styles['data'])
                current_row += 1
            current_row += 1

        # Datos principales
        if 'headers' in data_config and 'data' in data_config:
            # Escribir encabezados
            for col, header in enumerate(data_config['headers']):
                worksheet.write(current_row, col, header, styles['header'])

            # Ajustar ancho de columnas
            col_widths = data_config.get(
                'col_widths', [15] * len(data_config['headers']))
            for col, width in enumerate(col_widths):
                worksheet.set_column(col, col, width)

            current_row += 1

            # Escribir datos
            for row_idx, row_data in enumerate(data_config['data']):
                style = styles['data'] if row_idx % 2 == 0 else styles['data_alt']

                for col, value in enumerate(row_data):
                    # Determinar formato según el tipo de dato
                    if isinstance(value, (int, float)):
                        worksheet.write(current_row, col,
                                        value, styles['number'])
                    elif isinstance(value, datetime):
                        worksheet.write(current_row, col,
                                        value, styles['date'])
                    else:
                        worksheet.write(current_row, col, str(value), style)

                current_row += 1

            current_row += 2

        # Gráficos
        if 'charts' in data_config:
            for chart_config in data_config['charts']:
                current_row = self.add_chart_to_worksheet(
                    workbook, worksheet, chart_config, current_row)

        # Hojas adicionales
        if 'additional_sheets' in data_config:
            for sheet_config in data_config['additional_sheets']:
                additional_worksheet = workbook.add_worksheet(
                    sheet_config['name'])

                # Escribir datos de la hoja adicional
                if 'data' in sheet_config:
                    for row_idx, row_data in enumerate(sheet_config['data']):
                        for col_idx, cell_data in enumerate(row_data):
                            additional_worksheet.write(
                                row_idx, col_idx, cell_data)

        # Configuraciones finales
        worksheet.autofilter(data_config.get('autofilter_range', 'A1:Z1000'))
        worksheet.freeze_panes(data_config.get(
            'freeze_row', 0), data_config.get('freeze_col', 0))

        workbook.close()
        output.seek(0)

        response.write(output.read())
        output.close()

        return response


# Funciones de utilidad globales
def export_queryset_to_pdf(queryset, fields, title, filename=None, **kwargs):
    """Función utilitaria para exportar QuerySet a PDF"""
    if not filename:
        filename = f"{title.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

    # Preparar datos para la tabla
    headers = [field['label'] for field in fields]
    table_data = [headers]

    for obj in queryset:
        row = []
        for field in fields:
            value = getattr(obj, field['name'], '')
            if callable(value):
                value = value()
            row.append(str(value))
        table_data.append(row)

    # Configuración del PDF
    data_config = {
        'title': title,
        'table_data': table_data,
        'landscape': kwargs.get('landscape', len(headers) > 6),
        **kwargs
    }

    exporter = PDFExporter()
    return exporter.export_data_to_pdf(data_config, filename)


def export_queryset_to_excel(queryset, fields, title, filename=None, **kwargs):
    """Función utilitaria para exportar QuerySet a Excel"""
    if not filename:
        filename = f"{title.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

    # Preparar datos
    headers = [field['label'] for field in fields]
    data = []

    for obj in queryset:
        row = []
        for field in fields:
            value = getattr(obj, field['name'], '')
            if callable(value):
                value = value()
            row.append(value)
        data.append(row)

    # Configuración del Excel
    data_config = {
        'title': title,
        'headers': headers,
        'data': data,
        **kwargs
    }

    exporter = ExcelExporter()
    return exporter.export_data_to_excel(data_config, filename)
