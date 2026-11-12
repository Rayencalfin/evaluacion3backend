from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.timezone import localdate
from django.views.decorators.http import require_http_methods

from usuarios.models import Usuario

from .forms import CategoriaForm, HerramientaForm, UbicacionForm, UnidadFisicaForm
from .models import CambioUnidad, Categoria, Herramienta, Ubicacion, UnidadFisica


SECCIONES = {
    'categorias': ('Categorías', CategoriaForm, Categoria.objects.all()),
    'herramientas': (
        'Herramientas',
        HerramientaForm,
        Herramienta.objects.select_related('categoria'),
    ),
    'ubicaciones': ('Ubicaciones', UbicacionForm, Ubicacion.objects.all()),
    'unidades': (
        'Unidades físicas',
        UnidadFisicaForm,
        UnidadFisica.objects.select_related('herramienta', 'ubicacion'),
    ),
}


@login_required
@require_http_methods(['GET', 'POST'])
def gestionar(request, seccion='categorias', pk=None):
    if request.user.rol not in {Usuario.Rol.ADMINISTRADOR, Usuario.Rol.TRABAJADOR}:
        raise PermissionDenied

    if seccion not in SECCIONES:
        raise Http404

    titulo, formulario, consulta_base = SECCIONES[seccion]
    registros = consulta_base.all()
    datos = request.POST if request.method == 'POST' else None

    with transaction.atomic():
        consulta_objeto = registros
        if datos is not None and pk is not None and seccion in {'unidades', 'herramientas'}:
            consulta_objeto = registros.select_for_update(of=('self',))

        objeto = (
            get_object_or_404(consulta_objeto, pk=pk)
            if pk is not None
            else None
        )

        es_edicion_de_unidad = seccion == 'unidades' and objeto is not None
        estado_anterior = objeto.estado if es_edicion_de_unidad else None
        ubicacion_anterior = str(objeto.ubicacion) if es_edicion_de_unidad else None

        form = formulario(datos, instance=objeto)

        if datos is not None and form.is_valid():
            guardado = form.save()

            if seccion == 'herramientas':
                form.crear_unidades_faltantes(guardado)

            if es_edicion_de_unidad and {'estado', 'ubicacion'}.intersection(form.changed_data):
                CambioUnidad.objects.create(
                    unidad=guardado,
                    operador=request.user,
                    estado_anterior=estado_anterior,
                    estado_nuevo=guardado.estado,
                    ubicacion_anterior=ubicacion_anterior,
                    ubicacion_nueva=str(guardado.ubicacion),
                )

            return redirect('inventario:gestionar', seccion=seccion)

    historial = []
    busqueda_unidades = ''
    pagina_unidades = None

    if es_edicion_de_unidad:
        historial = objeto.cambios_manuales.select_related('operador')

    if seccion == 'unidades':
        busqueda_unidades = request.GET.get('q', '').strip()[:150]

        for termino in busqueda_unidades.split():
            registros = registros.filter(
                Q(codigo__icontains=termino)
                | Q(herramienta__nombre__icontains=termino)
            )

        registros = registros.order_by('codigo', 'pk')
        pagina_unidades = Paginator(registros, 10).get_page(
            request.GET.get('pagina')
        )
        registros = pagina_unidades.object_list

    return render(request, 'inventario/gestionar.html', {
        'titulo': titulo,
        'seccion': seccion,
        'secciones': [(clave, valores[0]) for clave, valores in SECCIONES.items()],
        'registros': registros,
        'busqueda_unidades': busqueda_unidades,
        'pagina_unidades': pagina_unidades,
        'objeto': objeto,
        'form': form,
        'historial': historial,
    })


def catalogo(request):
    categorias = Categoria.objects.filter(activa=True)
    herramientas = Herramienta.objects.filter(
        activa=True,
        categoria__activa=True,
    ).select_related('categoria').annotate(
        unidades_disponibles=Count(
            'unidades',
            filter=(
                Q(
                    unidades__estado=UnidadFisica.Estado.DISPONIBLE,
                    unidades__ubicacion__activa=True,
                )
                & ~UnidadFisica.criterio_mantenimiento(localdate(), 'unidades__')
            ),
        ),
    )

    categoria = request.GET.get('categoria', '')
    if categoria.isascii() and categoria.isdecimal() and len(categoria) <= 18:
        herramientas = herramientas.filter(categoria_id=int(categoria))

    busqueda = request.GET.get('q', '').strip()
    if busqueda:
        herramientas = herramientas.filter(
            Q(nombre__icontains=busqueda)
            | Q(marca__icontains=busqueda)
            | Q(modelo__icontains=busqueda)
        )

    return render(request, 'inventario/catalogo.html', {
        'herramientas': herramientas,
        'categorias': categorias,
        'categoria_seleccionada': categoria,
        'busqueda': busqueda,
    })