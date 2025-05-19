# usuarios/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('registro/', views.register_view, name='registro'),
    path('perfil/', views.profile_view, name='perfil'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
]
