from django.contrib.auth.models import AbstractUser
from django.db import models


class Usuario(AbstractUser):
    """Cuenta de acceso a Rentis."""

    class Rol(models.TextChoices):
        ADMINISTRADOR = 'ADMINISTRADOR', 'Administrador'
        TRABAJADOR = 'TRABAJADOR', 'Trabajador'
        CLIENTE = 'CLIENTE', 'Cliente o contratista'

    # Las cuentas nuevas serán clientes de forma predeterminada.
    rol = models.CharField(
        max_length=20,
        choices=Rol.choices,
        default=Rol.CLIENTE,
    )

    class Meta:
        verbose_name = 'usuario'
        verbose_name_plural = 'usuarios'

    def __str__(self):
        return f'{self.username} - {self.get_rol_display()}'