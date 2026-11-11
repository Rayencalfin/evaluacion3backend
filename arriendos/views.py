from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods, require_POST

from inventario.models import Herramienta, UnidadFisica
from usuarios.models import Usuario

from .forms import FechasForm, MovimientoForm
from .models import Arriendo, Movimiento


MENSAJE_ATRASO = 'Tienes una devolución atrasada. Regularízala para solicitar otro arriendo.'


def verificar_cliente(request):
    if request.user.rol != Usuario.Rol.CLIENTE:
        raise PermissionDenied


def unidades_disponibles(herramienta, inicio, termino):
    ocupadas = Arriendo.objects.filter(
        herramienta=herramienta,         estado__in=[
            Arriendo.Estado.SOLICITADO,
            Arriendo.Estado.APROBADO,
            Arriendo.Estado.ENTREGADO,
        ],
        inicio__lt=termino, termino__gt=inicio,
    ).values('unidad_id')
    return herramienta.unidades.filter(
        estado=UnidadFisica.Estado.DISPONIBLE, ubicacion__activa=True,
    ).exclude(pk__in=ocupadas).exclude(UnidadFisica.criterio_mantenimiento(termino))


@login_required
@require_http_methods(['GET', 'POST'])
def agregar(request, pk):
    verificar_cliente(request)
    herramienta = get_object_or_404(Herramienta, pk=pk, activa=True, categoria__activa=True)
    form = FechasForm(request.POST if request.method == 'POST' else None)
    if request.method == 'POST' and form.is_valid():
        if Arriendo.atrasados().filter(cliente=request.user).exists():
            form.add_error(None, MENSAJE_ATRASO)
        elif unidades_disponibles(herramienta, **form.cleaned_data).exists():
            Arriendo.objects.create(
                cliente=request.user, herramienta=herramienta,
                tarifa_diaria=herramienta.tarifa_diaria, **form.cleaned_data,
            )
            return redirect('arriendos:carrito')
        else:
            form.add_error(None, 'No hay unidades disponibles para esas fechas.')
    return render(request, 'arriendos/agregar.html', {'form': form, 'herramienta': herramienta})


def render_carrito(request, error=None):
    registros = Arriendo.objects.filter(cliente=request.user).select_related('herramienta')
    return render(request, 'arriendos/carrito.html', {
        'carrito': registros.filter(estado=Arriendo.Estado.CARRITO),
        'solicitudes': registros.exclude(estado=Arriendo.Estado.CARRITO).prefetch_related('movimientos'),
        'error': error,
        'bloqueado': Arriendo.atrasados().filter(cliente=request.user).exists(),
    })


@login_required
def carrito(request):
    verificar_cliente(request)
    return render_carrito(request)


@login_required
@require_POST
def quitar(request, pk):
    verificar_cliente(request)
    Arriendo.objects.filter(pk=pk, cliente=request.user, estado=Arriendo.Estado.CARRITO).delete()
    return redirect('arriendos:carrito')


@login_required
@require_POST
def solicitar(request):
    verificar_cliente(request)
    try:
        with transaction.atomic():
            if Arriendo.atrasados().filter(cliente=request.user).exists():
                raise ValidationError(MENSAJE_ATRASO)
            carrito = Arriendo.objects.filter(cliente=request.user, estado=Arriendo.Estado.CARRITO)
            ids = set(carrito.values_list('herramienta_id', flat=True))
            herramientas = Herramienta.objects.select_for_update(of=('self',)).select_related('categoria')
            modelos = herramientas.filter(pk__in=ids).order_by('pk').in_bulk()
            items = carrito.select_for_update().filter(herramienta_id__in=ids).order_by('pk')
            for item in items:
                herramienta = modelos[item.herramienta_id]
                if item.inicio < timezone.localdate():
                    raise ValidationError('Quita del carrito las solicitudes con fechas vencidas.')
                if not herramienta.activa or not herramienta.categoria.activa:
                    raise ValidationError(f'{herramienta.nombre} ya no está en el catálogo.')
                unidad = unidades_disponibles(herramienta, item.inicio, item.termino).order_by('pk').first()
                if unidad is None:
                    raise ValidationError(f'Ya no hay unidades de {herramienta.nombre} para esas fechas.')
                item.unidad = unidad
                item.estado = Arriendo.Estado.SOLICITADO
                item.save(update_fields=['unidad', 'estado'])
    except ValidationError as error:
        return render_carrito(request, error.message)
    return redirect('arriendos:carrito')


@login_required
def solicitudes(request):
    if request.user.rol not in {Usuario.Rol.ADMINISTRADOR, Usuario.Rol.TRABAJADOR}:
        raise PermissionDenied
    registros = Arriendo.objects.exclude(estado=Arriendo.Estado.CARRITO).select_related(
        'cliente', 'herramienta', 'unidad',
    ).prefetch_related('movimientos__operador')
    return render(request, 'arriendos/solicitudes.html', {'solicitudes': registros})


@login_required
@require_http_methods(['GET', 'POST'])
def registrar_movimiento(request, pk):
    if request.user.rol not in {Usuario.Rol.ADMINISTRADOR, Usuario.Rol.TRABAJADOR}:
        raise PermissionDenied 
    referencia = get_object_or_404(Arriendo, pk=pk)
    with transaction.atomic():
        Herramienta.objects.select_for_update().get(pk=referencia.herramienta_id)
        arriendo = get_object_or_404(
            Arriendo.objects.select_for_update().filter(
                   estado__in=[Arriendo.Estado.APROBADO, Arriendo.Estado.ENTREGADO],
                unidad__isnull=False,
            ),
            pk=pk,
        )
        entrega = arriendo.estado == Arriendo.Estado.APROBADO
        form = MovimientoForm(request.POST if request.method == 'POST' else None, entrega=entrega)
        if request.method == 'POST' and form.is_valid():
            unidad = UnidadFisica.objects.select_for_update().get(pk=arriendo.unidad_id)
            estado_esperado = UnidadFisica.Estado.DISPONIBLE if entrega else UnidadFisica.Estado.EN_USO
            hoy = timezone.localdate()
            if unidad.estado != estado_esperado:
                form.add_error(None, 'El estado actual de la unidad impide registrar este movimiento.')
            elif entrega and not arriendo.inicio <= hoy < arriendo.termino:
                form.add_error(None, 'La entrega debe registrarse dentro de las fechas del arriendo.')
            elif entrega and unidad.mantenimiento_pendiente:
                form.add_error(None, 'La unidad requiere mantenimiento preventivo.')
            else:
                horas = form.cleaned_data.get('horas_uso') or 0
                unidad.horas_uso_acumuladas += horas
                errores = unidad._meta.get_field('horas_uso_acumuladas').validators
                try:
                    for validar in errores:
                        validar(unidad.horas_uso_acumuladas)
                except ValidationError as error:
                    form.add_error('horas_uso', error)
                    return render(request, 'arriendos/movimiento.html', {
                        'arriendo': arriendo, 'form': form, 'entrega': entrega,
                    })
                dano = form.cleaned_data.get('danada', False)
                nuevo_estado = UnidadFisica.Estado.EN_USO if entrega else (
                    UnidadFisica.Estado.MANTENIMIENTO if dano or unidad.mantenimiento_pendiente else UnidadFisica.Estado.DISPONIBLE
                )
                dias_usados = max(1, (hoy - arriendo.inicio).days)
                dias_contratados = (arriendo.termino - arriendo.inicio).days
                reembolso = max(0, dias_contratados - dias_usados) * arriendo.tarifa_diaria
                Movimiento.objects.create(
                    arriendo=arriendo, operador=request.user,
                    tipo=Movimiento.Tipo.ENTREGA if entrega else Movimiento.Tipo.DEVOLUCION,
                    firma=form.cleaned_data['firma'], observaciones=form.cleaned_data['observaciones'],
                        firma_dibujada=form.cleaned_data['firma_dibujada'],
                    estado_anterior=unidad.estado, estado_nuevo=nuevo_estado,
                    cargo_dano=unidad.valor_reposicion if dano else 0,
                    reembolso=0 if entrega else reembolso,
                )
                unidad.estado = nuevo_estado
                unidad.save(update_fields=['estado', 'horas_uso_acumuladas'])
                arriendo.estado = Arriendo.Estado.ENTREGADO if entrega else Arriendo.Estado.DEVUELTO
                arriendo.save(update_fields=['estado'])
                return redirect('arriendos:solicitudes')

        return render(request, 'arriendos/movimiento.html', {
            'arriendo': arriendo, 'form': form, 'entrega': entrega,
        })
@login_required
@require_POST
def cambiar_estado_solicitud(request, pk, accion):
    estados = Arriendo.Estado
    personal = {Usuario.Rol.ADMINISTRADOR, Usuario.Rol.TRABAJADOR}

    if accion == 'cancelar':
        verificar_cliente(request)
        solicitudes_del_usuario = Arriendo.objects.filter(cliente=request.user)
        estados_permitidos = {estados.SOLICITADO, estados.APROBADO}
        nuevo_estado = estados.CANCELADO
        destino = 'arriendos:carrito'
    elif accion in {'aprobar', 'rechazar'}:
        if request.user.rol not in personal:
            raise PermissionDenied
        solicitudes_del_usuario = Arriendo.objects.all()
        estados_permitidos = {estados.SOLICITADO}
        nuevo_estado = estados.APROBADO if accion == 'aprobar' else estados.RECHAZADO
        destino = 'arriendos:solicitudes'
    else:
        return redirect('usuarios:panel')

    referencia = get_object_or_404(solicitudes_del_usuario, pk=pk)

    with transaction.atomic():
        Herramienta.objects.select_for_update().get(pk=referencia.herramienta_id)
        arriendo = get_object_or_404(
            solicitudes_del_usuario.select_for_update(),
            pk=pk,
        )
        if arriendo.estado in estados_permitidos:
            arriendo.estado = nuevo_estado
            arriendo.save(update_fields=['estado'])

    return redirect(destino)