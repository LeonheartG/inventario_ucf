# usuarios/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Ruta principal que redirige según el estado de autenticación
    path('', views.index, name='index'),

    # Rutas de autenticación
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('registro/', views.register_view, name='registro'),

    # Rutas protegidas
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('perfil/', views.profile_view, name='perfil'),
    path('cambiar-password/', views.cambiar_password_view, name='cambiar_password'),
]
