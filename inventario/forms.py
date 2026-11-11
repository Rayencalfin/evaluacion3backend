from django import forms
from django.core.validators import RegexValidator
from .models import Categoria, Herramienta, Ubicacion, UnidadFisica


class CategoriaForm(forms.ModelForm):
    """Formulario para crear y editar categorías."""

    class Meta:
        model = Categoria
        fields = ['nombre', 'descripcion', 'activa']
        labels = {
            'nombre': 'Nombre de la categoría',
            'descripcion': 'Descripción',
            'activa': 'Categoría activa',
        }
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 3}),
        }

    def clean_nombre(self):
        nombre = self.cleaned_data['nombre'].strip()

        categorias = Categoria.objects.filter(nombre__iexact=nombre)

        if self.instance.pk:
            categorias = categorias.exclude(pk=self.instance.pk)

        if categorias.exists():
            raise forms.ValidationError(
                'Ya existe una categoría con este nombre.'
            )

        return nombre
class HerramientaForm(forms.ModelForm):
    prefijo_inventario = forms.CharField(
        label='Prefijo de inventario',
        max_length=12,
        required=False,
        help_text='Ejemplo: MA para generar MA-01, MA-02 y siguientes.',
        validators=[RegexValidator(
            r'\A[A-Za-z0-9]+\Z',
            'Usa solo letras y números, sin guiones ni espacios.',
        )],
    )
    cantidad_total = forms.IntegerField(
        label='Cantidad total de unidades activas',
        min_value=0,
        help_text='Incluye las unidades disponibles, en uso y en mantenimiento.',
    )
    ubicacion_inicial = forms.ModelChoiceField(
        label='Ubicación de las nuevas unidades',
        queryset=Ubicacion.objects.filter(activa=True),
        required=False,
    )
    valor_reposicion_unidad = forms.IntegerField(
        label='Valor de reposición por unidad (CLP)',
        min_value=1,
        max_value=999_999_999_999,
        required=False,
    )

    class Meta:
        model = Herramienta
        fields = [
            'categoria', 'nombre', 'marca', 'modelo', 'descripcion',
            'imagen_url', 'tarifa_diaria', 'activa', 'prefijo_inventario',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cantidad_actual = 0
        if self.instance.pk:
            self.cantidad_actual = self.instance.unidades.exclude(
                estado=UnidadFisica.Estado.DADO_DE_BAJA,
            ).count()

        self.initial['cantidad_total'] = self.cantidad_actual
        if self.instance.prefijo_inventario:
            self.fields['prefijo_inventario'].disabled = True

    def clean_prefijo_inventario(self):
        return self.cleaned_data['prefijo_inventario'].upper() or None

    def clean(self):
        datos = super().clean()
        cantidad = datos.get('cantidad_total')

        if cantidad is None:
            return datos

        if cantidad < self.cantidad_actual:
            self.add_error(
                'cantidad_total',
                'Para reducir el total, da de baja las unidades específicas desde Unidades físicas.',
            )
        elif cantidad > self.cantidad_actual:
            for campo in (
                'prefijo_inventario',
                'ubicacion_inicial',
                'valor_reposicion_unidad',
            ):
                if campo not in self.errors and not datos.get(campo):
                    self.add_error(campo, 'Completa este campo para crear las unidades.')

        return datos

    def crear_unidades_faltantes(self, herramienta):
        faltantes = self.cleaned_data['cantidad_total'] - self.cantidad_actual
        if faltantes <= 0:
            return

        correlativo = herramienta.ultimo_correlativo
        nuevas = []
        while len(nuevas) < faltantes:
            correlativo += 1
            codigo = f'{herramienta.prefijo_inventario}-{correlativo:02d}'

            if UnidadFisica.objects.filter(codigo=codigo).exists():
                continue

            nuevas.append(UnidadFisica(
                codigo=codigo,
                herramienta=herramienta,
                ubicacion=self.cleaned_data['ubicacion_inicial'],
                valor_reposicion=self.cleaned_data['valor_reposicion_unidad'],
            ))

        UnidadFisica.objects.bulk_create(nuevas)
        herramienta.ultimo_correlativo = correlativo
        herramienta.save(update_fields=['ultimo_correlativo'])

class UbicacionForm(forms.ModelForm):
    class Meta:
        model = Ubicacion
        fields = ['codigo', 'nombre', 'tipo', 'direccion', 'activa']


class UnidadFisicaForm(forms.ModelForm):
    class Meta:
        model = UnidadFisica
        fields = ['herramienta', 'ubicacion', 'numero_serie', 'estado',
                  'valor_reposicion', 'horas_uso_acumuladas', 'mantenimiento_fecha',
                  'mantenimiento_horas', 'observaciones']
        widgets = {
            'mantenimiento_fecha': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
        }
