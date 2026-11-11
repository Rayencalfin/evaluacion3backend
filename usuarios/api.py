from drf_spectacular.utils import extend_schema
from rest_framework import permissions, serializers, views
from rest_framework.response import Response
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView


class AccesoSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['rol'] = user.rol
        return token


class AccesoJWT(TokenObtainPairView):
    serializer_class = AccesoSerializer


class PerfilSerializer(serializers.Serializer):
    username = serializers.CharField()
    rol = serializers.CharField()


class PerfilAPI(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses=PerfilSerializer)
    def get(self, request):
        return Response(PerfilSerializer(request.user).data)
