# reportes/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='reportes_index'),

    # Reportes
    path('inventario/', views.inventario_report, name='inventario_report'),
    path('inventario/categoria/', views.inventario_categoria_report,
         name='inventario_categoria_report'),
    path('inventario/ubicacion/', views.inventario_ubicacion_report,
         name='inventario_ubicacion_report'),
    path('mantenimiento/', views.mantenimiento_report,
         name='mantenimiento_report'),
    path('obsolescencia/', views.obsolescencia_report,
         name='obsolescencia_report'),
    path('transformacion-digital/', views.transformacion_digital_report,
         name='transformacion_digital_report'),

    # Dashboard
    path('dashboard/', views.dashboard, name='reportes_dashboard'),

    # Exportaciones
    path('export/inventario/<str:format>/',
         views.export_inventario, name='export_inventario'),
    path('export/mantenimiento/<str:format>/',
         views.export_mantenimiento, name='export_mantenimiento'),
    path('export/diagnostico/<str:format>/',
         views.export_diagnostico, name='export_diagnostico'),
]
