from django.urls import path
from . import views

app_name = 'arriendos'
urlpatterns = [
    path('carrito/', views.carrito, name='carrito'),
    path('agregar/<int:pk>/', views.agregar, name='agregar'),
    path('quitar/<int:pk>/', views.quitar, name='quitar'),
    path('solicitar/', views.solicitar, name='solicitar'),
    path('solicitudes/', views.solicitudes, name='solicitudes'),
    path('solicitudes/<int:pk>/movimiento/', views.registrar_movimiento, name='movimiento'),
        path(
        'solicitudes/<int:pk>/estado/<slug:accion>/',
        views.cambiar_estado_solicitud,
        name='cambiar_estado',
    ),
]
