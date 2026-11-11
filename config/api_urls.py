from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import PermissionDenied
from django.urls import path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from rest_framework_simplejwt.views import TokenRefreshView

from usuarios.api import AccesoJWT, PerfilAPI
from usuarios.models import Usuario


def es_administrador(usuario):
    if usuario.rol != Usuario.Rol.ADMINISTRADOR:
        raise PermissionDenied
    return True


def documentacion(vista):
    return login_required(user_passes_test(es_administrador)(vista))


urlpatterns = [
    path('token/', AccesoJWT.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('perfil/', PerfilAPI.as_view(), name='api_perfil'),
    path('esquema/', documentacion(SpectacularAPIView.as_view()), name='api_esquema'),
    path('swagger/', documentacion(SpectacularSwaggerView.as_view(url_name='api_esquema')), name='api_swagger'),
    path('redoc/', documentacion(SpectacularRedocView.as_view(url_name='api_esquema')), name='api_redoc'),
]
