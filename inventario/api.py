from rest_framework import generics, permissions, serializers

from .models import Herramienta


class HerramientaSerializer(serializers.ModelSerializer):
    categoria = serializers.CharField(source='categoria.nombre', read_only=True)

    class Meta:
        model = Herramienta
        fields = ['id', 'categoria', 'nombre', 'marca', 'modelo', 'descripcion',
                  'imagen_url', 'tarifa_diaria']


class CatalogoAPIView(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = HerramientaSerializer
    queryset = Herramienta.objects.filter(
        activa=True, categoria__activa=True,
    ).select_related('categoria')
