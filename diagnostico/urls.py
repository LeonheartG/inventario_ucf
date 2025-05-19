# diagnostico/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='diagnostico_index'),

    # Cuestionarios
    path('cuestionarios/', views.cuestionario_list, name='cuestionario_list'),
    path('cuestionarios/new/', views.cuestionario_create, name='cuestionario_new'),
    path('cuestionarios/<int:pk>/', views.cuestionario_detail,
         name='cuestionario_detail'),
    path('cuestionarios/<int:pk>/edit/',
         views.cuestionario_update, name='cuestionario_edit'),
    path('cuestionarios/<int:pk>/delete/',
         views.cuestionario_delete, name='cuestionario_delete'),

    # Evaluaciones
    path('evaluaciones/', views.evaluacion_list, name='evaluacion_list'),
    path('evaluaciones/new/', views.evaluacion_create, name='evaluacion_new'),
    path('evaluaciones/<int:pk>/', views.evaluacion_detail,
         name='evaluacion_detail'),
    path('evaluaciones/<int:pk>/edit/',
         views.evaluacion_update, name='evaluacion_edit'),
    path('evaluaciones/<int:pk>/respuestas/',
         views.evaluacion_respuestas, name='evaluacion_respuestas'),

    # Indicadores
    path('indicadores/', views.indicador_list, name='indicador_list'),
    path('indicadores/<int:pk>/', views.indicador_detail, name='indicador_detail'),
]
