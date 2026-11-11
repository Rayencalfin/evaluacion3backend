import uuid
from decimal import Decimal

from django.core.validators import MinValueValidator
from django.conf import settings
from django.db import models


def generar_codigo_unidad():
    """Genera un identificador de inventario automáticamente."""
    return f'EQ-{uuid.uuid4().hex.upper()}'


class Categoria(models.Model):
    """Clasifica los modelos de herramientas."""

    nombre = models.CharField(
        max_length=100,
        unique=True,
    )
    descripcion = models.TextField(blank=True)
    activa = models.BooleanField(default=True)

    class Meta:
        ordering = ['nombre']
        verbose_name = 'categoría'
        verbose_name_plural = 'categorías'

    def __str__(self):
        return self.nombre


class Herramienta(models.Model):
    """Ficha del catálogo compartida por varias unidades físicas."""

    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.PROTECT,
        related_name='herramientas',
    )
    nombre = models.CharField(max_length=150)
    marca = models.CharField(max_length=100)
    modelo = models.CharField(max_length=100)
    descripcion = models.TextField()

    # Enlace externo a la imagen del catálogo.
    imagen_url = models.URLField(
        max_length=1000,
        blank=True,
    )

    # Importe en pesos chilenos por cada bloque de 24 horas.
    tarifa_diaria = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        validators=[MinValueValidator(Decimal('1'))],
    )

    activa = models.BooleanField(default=True)
    creada_en = models.DateTimeField(auto_now_add=True)
    actualizada_en = models.DateTimeField(auto_now=True)
    prefijo_inventario = models.CharField(
        max_length=12,
        unique=True,
        null=True,
        blank=True,
    )
    ultimo_correlativo = models.PositiveIntegerField(default=0, editable=False)

    class Meta:
        ordering = ['nombre', 'marca', 'modelo']
        verbose_name = 'herramienta'
        verbose_name_plural = 'herramientas'
        constraints = [
            models.CheckConstraint(
                condition=models.Q(tarifa_diaria__gte=1),
                name='herramienta_tarifa_positiva',
            ),
        ]

    def __str__(self):
        return f'{self.nombre} - {self.marca} {self.modelo}'


class Ubicacion(models.Model):
    """Obra o bodega donde puede encontrarse una unidad física."""

    class Tipo(models.TextChoices):
        BODEGA = 'BODEGA', 'Bodega'
        OBRA = 'OBRA', 'Obra'

    codigo = models.CharField(
        max_length=30,
        unique=True,
    )
    nombre = models.CharField(max_length=150)
    tipo = models.CharField(
        max_length=10,
        choices=Tipo.choices,
    )
    direccion = models.CharField(max_length=250)
    activa = models.BooleanField(default=True)

    class Meta:
        ordering = ['tipo', 'nombre']
        verbose_name = 'ubicación'
        verbose_name_plural = 'ubicaciones'

    def __str__(self):
        return f'{self.codigo} - {self.nombre}'


class UnidadFisica(models.Model):
    """Equipo real con identificación e historial propios."""

    class Estado(models.TextChoices):
        DISPONIBLE = 'DISPONIBLE', 'Disponible'
        EN_USO = 'EN_USO', 'En Uso'
        MANTENIMIENTO = 'MANTENIMIENTO', 'Mantenimiento'
        DADO_DE_BAJA = 'DADO_DE_BAJA', 'Dado de Baja'

    codigo = models.CharField(
        max_length=35,
        unique=True,
        default=generar_codigo_unidad,
        editable=False,
    )

    herramienta = models.ForeignKey(
        Herramienta,
        on_delete=models.PROTECT,
        related_name='unidades',
    )

    ubicacion = models.ForeignKey(
        Ubicacion,
        on_delete=models.PROTECT,
        related_name='unidades',
    )

    numero_serie = models.CharField(
        max_length=100,
        blank=True,
    )

    estado = models.CharField(
        max_length=20,
        choices=Estado.choices,
        default=Estado.DISPONIBLE,
    )

    valor_reposicion = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        validators=[MinValueValidator(Decimal('1'))],
    )

    horas_uso_acumuladas = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0'),
        validators=[MinValueValidator(Decimal('0'))],
    )

    mantenimiento_fecha = models.DateField('Próximo mantenimiento', null=True, blank=True)
    mantenimiento_horas = models.DecimalField(
        'Próximo mantenimiento al alcanzar estas horas acumuladas',
        max_digits=12, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(Decimal('0.01'))],
    )
    observaciones = models.TextField(blank=True)
    creada_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['codigo']
        verbose_name = 'unidad física'
        verbose_name_plural = 'unidades físicas'
        constraints = [
            models.CheckConstraint(
                condition=models.Q(valor_reposicion__gte=1),
                name='unidad_reposicion_positiva',
            ),
            models.CheckConstraint(
                condition=models.Q(horas_uso_acumuladas__gte=0),
                name='unidad_horas_no_negativas',
            ),
        ]

    @staticmethod
    def criterio_mantenimiento(fecha, prefijo=''):
        return (
            models.Q(**{f'{prefijo}mantenimiento_fecha__lte': fecha})
            | models.Q(**{
                f'{prefijo}mantenimiento_horas__lte': models.F(f'{prefijo}horas_uso_acumuladas'),
            })
        )

    @property
    def mantenimiento_pendiente(self):
        from django.utils.timezone import localdate

        return (
            self.mantenimiento_fecha is not None and self.mantenimiento_fecha <= localdate()
            or self.mantenimiento_horas is not None
            and self.horas_uso_acumuladas >= self.mantenimiento_horas
        )

    def __str__(self):
        return f'{self.codigo} - {self.herramienta}'

class CambioUnidad(models.Model):
    unidad = models.ForeignKey(UnidadFisica, on_delete=models.PROTECT, related_name='cambios_manuales')
    operador = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    estado_anterior = models.CharField(max_length=20)
    estado_nuevo = models.CharField(max_length=20)
    ubicacion_anterior = models.CharField(max_length=200)
    ubicacion_nueva = models.CharField(max_length=200)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha', '-pk']
