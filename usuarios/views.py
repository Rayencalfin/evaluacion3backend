from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from arriendos.models import Arriendo
from inventario.models import UnidadFisica
from .forms import GestionUsuarioForm, RegistroClienteForm

from .models import Usuario


@login_required
def panel(request):
    titulos = {
        Usuario.Rol.ADMINISTRADOR: 'Panel administrativo',
        Usuario.Rol.TRABAJADOR: 'Panel operativo',
        Usuario.Rol.CLIENTE: 'Mi cuenta',
    }

    titulo = titulos.get(request.user.rol)
    if titulo is None:
        raise PermissionDenied('Tu cuenta no tiene un rol válido.')

    contexto = {'titulo_panel': titulo}

    if request.user.rol == Usuario.Rol.ADMINISTRADOR:
        conteos = {
            fila['estado']: fila['cantidad']
            for fila in UnidadFisica.objects.values('estado').annotate(
                cantidad=Count('pk')
            )
        }
        contexto.update(
            total_unidades=sum(conteos.values()),
            solicitudes_pendientes=Arriendo.objects.filter(
                estado=Arriendo.Estado.SOLICITADO
            ).count(),
            atrasos=Arriendo.atrasados().count(),
            estados=[
                (estado.label, conteos.get(estado.value, 0))
                for estado in UnidadFisica.Estado
            ],
        )

    return render(request, 'usuarios/panel.html', contexto)

def registro(request):
    """Permite crear una cuenta de cliente."""

    if request.user.is_authenticated:
        return redirect('usuarios:panel')

    if request.method == 'POST':
        formulario = RegistroClienteForm(request.POST)

        if formulario.is_valid():
            formulario.save()
            return redirect('usuarios:login')
    else:
        formulario = RegistroClienteForm()

    return render(request, 'usuarios/registro.html', {
        'form': formulario,
    })

@login_required
@require_http_methods(['GET', 'POST'])
def gestion_usuarios(request, pk=None):
    if request.user.rol != Usuario.Rol.ADMINISTRADOR:
        raise PermissionDenied
    cuenta = get_object_or_404(Usuario, pk=pk) if pk is not None else None
    form = None
    if cuenta is not None:
        if cuenta.pk == request.user.pk or cuenta.is_superuser:
            raise PermissionDenied
        form = GestionUsuarioForm(request.POST if request.method == 'POST' else None, instance=cuenta)
        if request.method == 'POST' and form.is_valid():
            form.save()
            return redirect('usuarios:gestion')
    return render(request, 'usuarios/gestion.html', {
        'cuentas': Usuario.objects.order_by('username'), 'cuenta': cuenta, 'form': form,
    })


@login_required
def reportes(request):
    if request.user.rol != Usuario.Rol.ADMINISTRADOR:
        raise PermissionDenied
    unidades = UnidadFisica.objects.values('estado').annotate(cantidad=Count('pk'))
    arriendos = Arriendo.objects.exclude(estado=Arriendo.Estado.CARRITO).values('estado').annotate(cantidad=Count('pk'))
    resumen = [
        ('Unidades físicas', [(UnidadFisica.Estado(fila['estado']).label, fila['cantidad']) for fila in unidades]),
        ('Arriendos', [(Arriendo.Estado(fila['estado']).label, fila['cantidad']) for fila in arriendos]),
    ]
    return render(request, 'usuarios/reportes.html', {'resumen': resumen, 'atrasos': Arriendo.atrasados().count()})
