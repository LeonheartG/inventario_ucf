# inventario/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='inventario_index'),

    # Hardware
    path('hardware/', views.hardware_list, name='hardware_list'),
    path('hardware/new/', views.hardware_create, name='hardware_new'),
    path('hardware/<int:pk>/', views.hardware_detail, name='hardware_detail'),
    path('hardware/<int:pk>/edit/', views.hardware_update, name='hardware_edit'),
    path('hardware/<int:pk>/delete/',
         views.hardware_delete, name='hardware_delete'),

    # Software
    path('software/', views.software_list, name='software_list'),
    path('software/new/', views.software_create, name='software_new'),
    path('software/<int:pk>/', views.software_detail, name='software_detail'),
    path('software/<int:pk>/edit/', views.software_update, name='software_edit'),
    path('software/<int:pk>/delete/',
         views.software_delete, name='software_delete'),

    # Mantenimiento
    path('mantenimiento/', views.mantenimiento_list, name='mantenimiento_list'),
    path('mantenimiento/new/', views.mantenimiento_create,
         name='mantenimiento_new'),
    path('mantenimiento/<int:pk>/', views.mantenimiento_detail,
         name='mantenimiento_detail'),
    path('mantenimiento/<int:pk>/edit/',
         views.mantenimiento_update, name='mantenimiento_edit'),
    path('mantenimiento/<int:pk>/delete/',
         views.mantenimiento_delete, name='mantenimiento_delete'),
]
