from django.conf import settings
from django.db import models
from django.db.models import F, Q
from django.utils.timezone import localdate
from base64 import b64encode


class Arriendo(models.Model):
    class Estado(models.TextChoices):
        CARRITO = 'CARRITO', 'En carrito'
        SOLICITADO = 'SOLICITADO', 'Solicitado'
        APROBADO = 'APROBADO', 'Aprobado'
        RECHAZADO = 'RECHAZADO', 'Rechazado'
        CANCELADO = 'CANCELADO', 'Cancelado'
        ENTREGADO = 'ENTREGADO', 'Entregado'
        DEVUELTO = 'DEVUELTO', 'Devuelto'

    cliente = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    herramienta = models.ForeignKey('inventario.Herramienta', on_delete=models.PROTECT)
    unidad = models.ForeignKey('inventario.UnidadFisica', on_delete=models.PROTECT, null=True)
    inicio = models.DateField()
    termino = models.DateField()
    tarifa_diaria = models.DecimalField(max_digits=12, decimal_places=0)
    estado = models.CharField(max_length=12, choices=Estado.choices, default=Estado.CARRITO)

    class Meta:
        ordering = ['pk']
        constraints = [
            models.CheckConstraint(condition=Q(termino__gt=F('inicio')), name='arriendo_fechas_validas'),
        ]
        indexes = [models.Index(fields=['unidad', 'estado', 'inicio', 'termino'])]

    @classmethod
    def atrasados(cls):
        return cls.objects.filter(estado=cls.Estado.ENTREGADO, termino__lt=localdate())

    @property
    def atrasado(self):
        return self.estado == self.Estado.ENTREGADO and self.termino < localdate()

    @property
    def devolucion(self):
        return next((movimiento for movimiento in self.movimientos.all()
                     if movimiento.tipo == Movimiento.Tipo.DEVOLUCION), None)

    @property
    def total(self):
        return (self.termino - self.inicio).days * self.tarifa_diaria


class Movimiento(models.Model):
    class Tipo(models.TextChoices):
        ENTREGA = 'ENTREGA', 'Entrega'
        DEVOLUCION = 'DEVOLUCION', 'Devolución'

    arriendo = models.ForeignKey(Arriendo, on_delete=models.PROTECT, related_name='movimientos')
    operador = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    tipo = models.CharField(max_length=10, choices=Tipo.choices)
    firma = models.CharField(max_length=150)
    firma_dibujada = models.BinaryField(blank=True, null=True, editable=False)
    observaciones = models.TextField(blank=True)
    estado_anterior = models.CharField(max_length=20)
    estado_nuevo = models.CharField(max_length=20)
    registrado_en = models.DateTimeField(auto_now_add=True)
    cargo_dano = models.DecimalField(max_digits=12, decimal_places=0, default=0)

    reembolso = models.DecimalField(max_digits=20, decimal_places=0, default=0)
    @property
    def firma_png_base64(self):
        if self.firma_dibujada:
            return b64encode(self.firma_dibujada).decode('ascii')
        return ''
    
    class Meta:
        ordering = ['registrado_en', 'pk']
        constraints = [
            models.UniqueConstraint(fields=['arriendo', 'tipo'], name='movimiento_unico_por_arriendo'),
        ]
