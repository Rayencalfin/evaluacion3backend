"""Rutas principales de Rentis."""

from django.urls import include, path

urlpatterns = [
    path('api/', include('config.api_urls')),
    path('', include('core.urls')),
    path('', include('inventario.urls')),
    path('arriendos/', include('arriendos.urls')),
    path('cuenta/', include('usuarios.urls')),
]