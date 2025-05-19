# inventario_ucf/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('usuarios/', include('usuarios.urls')),
    path('inventario/', include('inventario.urls')),
    path('locales/', include('locales.urls')),
    path('diagnostico/', include('diagnostico.urls')),
    path('reportes/', include('reportes.urls')),
    path('', include('usuarios.urls')),  # La ruta raíz redirigirá a usuarios
]

# Configuración para servir archivos multimedia en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
