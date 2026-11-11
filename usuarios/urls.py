from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path

from . import views

app_name = 'usuarios'

urlpatterns = [
    path('gestion/', views.gestion_usuarios, name='gestion'),
    path('gestion/<int:pk>/', views.gestion_usuarios, name='editar_cuenta'),
    path('reportes/', views.reportes, name='reportes'),
    path(
        'login/',
        LoginView.as_view(
            template_name='usuarios/login.html',
            redirect_authenticated_user=True,
        ),
        name='login',
    ),
    path('registro/', views.registro, name='registro'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('panel/', views.panel, name='panel'),
]