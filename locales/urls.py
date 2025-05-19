# locales/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='locales_index'),

    # Locales
    path('locales/', views.local_list, name='local_list'),
    path('locales/new/', views.local_create, name='local_new'),
    path('locales/<int:pk>/', views.local_detail, name='local_detail'),
    path('locales/<int:pk>/edit/', views.local_update, name='local_edit'),
    path('locales/<int:pk>/delete/', views.local_delete, name='local_delete'),

    # Equipamiento
    path('equipamiento/', views.equipamiento_list, name='equipamiento_list'),
    path('equipamiento/new/', views.equipamiento_create, name='equipamiento_new'),
    path('equipamiento/<int:pk>/', views.equipamiento_detail,
         name='equipamiento_detail'),
    path('equipamiento/<int:pk>/edit/',
         views.equipamiento_update, name='equipamiento_edit'),
    path('equipamiento/<int:pk>/delete/',
         views.equipamiento_delete, name='equipamiento_delete'),
]
