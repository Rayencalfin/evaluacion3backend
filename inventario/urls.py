from django.urls import path

from . import views
from .api import CatalogoAPIView

app_name = 'inventario'

urlpatterns = [
    path('api/catalogo/', CatalogoAPIView.as_view(), name='api_catalogo'),
    path('catalogo/', views.catalogo, name='catalogo'),
    path('inventario/', views.gestionar, name='inicio'),
    path('inventario/<slug:seccion>/', views.gestionar, name='gestionar'),
    path('inventario/<slug:seccion>/<int:pk>/editar/', views.gestionar, name='editar'),
]
