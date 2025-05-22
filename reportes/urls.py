# reportes/urls.py
from django.urls import path
from . import views

# Todas las vistas de reportes requieren permisos especiales
urlpatterns = [
    # Dashboard principal de reportes
    path('', views.reportes_index_view, name='reportes_index'),
    path('dashboard/', views.dashboard_view, name='reportes_dashboard'),

    # Reportes de inventario
    path('inventario/', views.inventario_report_view, name='inventario_report'),
    path('inventario/resultado/', views.inventario_report_result_view,
         name='inventario_report_result'),
    path('inventario/categoria/', views.inventario_categoria_report_view,
         name='inventario_categoria_report'),
    path('inventario/ubicacion/', views.inventario_ubicacion_report_view,
         name='inventario_ubicacion_report'),
    path('obsolescencia/', views.obsolescencia_report_view,
         name='obsolescencia_report'),

    # Reportes de mantenimiento
    path('mantenimiento/', views.mantenimiento_report_view,
         name='mantenimiento_report'),
    path('mantenimiento/resultado/', views.mantenimiento_report_result_view,
         name='mantenimiento_report_result'),

    # Reportes de transformación digital
    path('transformacion-digital/', views.transformacion_digital_report_view,
         name='transformacion_digital_report'),
    path('transformacion-digital/resultado/', views.transformacion_digital_report_result_view,
         name='transformacion_digital_report_result'),

    # Exportaciones (también protegidas)
    path('export/inventario/<str:format>/',
         views.export_inventario_view, name='export_inventario'),
    path('export/mantenimiento/<str:format>/',
         views.export_mantenimiento_view, name='export_mantenimiento'),
    path('export/diagnostico/<str:format>/',
         views.export_diagnostico_view, name='export_diagnostico'),
]
