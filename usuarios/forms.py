from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import Usuario


class RegistroClienteForm(UserCreationForm):
    """Registro público sin campos para modificar roles o permisos."""

    class Meta:
        model = Usuario
        fields = [
            'username',
            'first_name',
            'last_name',
            'email',
        ]
        labels = {
            'username': 'Nombre de usuario',
            'first_name': 'Nombre',
            'last_name': 'Apellidos',
            'email': 'Correo electrónico',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Estos datos serán obligatorios en el registro público.
        for campo in ['first_name', 'last_name', 'email']:
            self.fields[campo].required = True

    def save(self, commit=True):
        usuario = super().save(commit=False)

        # El servidor fija el rol y evita privilegios administrativos.
        usuario.rol = Usuario.Rol.CLIENTE
        usuario.is_staff = False
        usuario.is_superuser = False

        if commit:
            usuario.save()

        return usuario

class GestionUsuarioForm(forms.ModelForm):
    class Meta:
        model = Usuario
        fields = ['rol', 'is_active']
        labels = {'is_active': 'Cuenta activa'}

class DatosClienteForm(forms.ModelForm):
    email = forms.EmailField(label='Correo electrónico')

    class Meta:
        model = Usuario
        fields = ['first_name', 'last_name', 'email']
        labels = {
            'first_name': 'Nombre',
            'last_name': 'Apellidos',
        }