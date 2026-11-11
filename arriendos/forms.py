from django import forms
from django.utils import timezone
from base64 import b64decode
from binascii import Error as ErrorBase64
from io import BytesIO

from PIL import Image, ImageChops, UnidentifiedImageError

class FechasForm(forms.Form):
    inicio = forms.DateField(label='Fecha de retiro', widget=forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'))
    termino = forms.DateField(label='Fecha de devolución', widget=forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'))

    def clean(self):
        datos = super().clean()
        inicio = datos.get('inicio')
        termino = datos.get('termino')
        if inicio and inicio < timezone.localdate():
            self.add_error('inicio', 'El retiro debe ser hoy o en una fecha futura.')
        if inicio and termino and termino <= inicio:
            self.add_error('termino', 'La devolución debe ser posterior al retiro.')
        return datos


class MovimientoForm(forms.Form):
    firma = forms.CharField(label='Nombre completo del responsable de obra', max_length=150)
    firma_dibujada = forms.CharField(
        label='Firma dibujada',
        widget=forms.HiddenInput,
        max_length=350_000,
        error_messages={'required': 'Dibuja la firma antes de confirmar.'},
    )
    confirmacion = forms.BooleanField(label='Confirmo este movimiento con mi nombre')
    observaciones = forms.CharField(label='Observaciones', required=False, widget=forms.Textarea(attrs={'rows': 3}))
    horas_uso = forms.DecimalField(
        label='Horas de uso durante este arriendo', min_value=0,
        max_digits=12, decimal_places=2, required=False,
    )
    danada = forms.BooleanField(label='La herramienta se devolvió dañada', required=False)

    def __init__(self, *args, entrega, **kwargs):
        super().__init__(*args, **kwargs)
        if entrega:
            self.fields.pop('danada')
            self.fields.pop('horas_uso')
    def clean_firma_dibujada(self):
        valor = self.cleaned_data['firma_dibujada']
        prefijo, _, contenido = valor.partition(',')

        if prefijo != 'data:image/png;base64':
            raise forms.ValidationError('Vuelve a dibujar la firma.')

        try:
            datos = b64decode(contenido, validate=True)
            with Image.open(BytesIO(datos), formats=['PNG']) as imagen:
                if imagen.size != (600, 220):
                    raise forms.ValidationError('El tamaño de la firma no es válido.')
                firma = imagen.convert('RGBA')
        except (ErrorBase64, UnidentifiedImageError, OSError, ValueError,
                Image.DecompressionBombError) as error:
            raise forms.ValidationError('La imagen de la firma no es válida.') from error

        fondo = Image.new('RGBA', firma.size, 'white')
        fondo.alpha_composite(firma)
        firma_visible = fondo.convert('RGB')
        blanco = Image.new('RGB', firma.size, 'white')

        if ImageChops.difference(firma_visible, blanco).getbbox() is None:
            raise forms.ValidationError('Dibuja la firma antes de confirmar.')

        salida = BytesIO()
        firma_visible.save(salida, format='PNG')
        return salida.getvalue()