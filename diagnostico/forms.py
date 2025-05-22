# diagnostico/forms.py
from django import forms
from .models import Cuestionario, Pregunta, Diagnostico, Respuesta, IndicadorDiagnostico
from usuarios.models import Departamento


class CuestionarioForm(forms.ModelForm):
    class Meta:
        model = Cuestionario
        fields = ['titulo', 'descripcion', 'activo']
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 3}),
        }


class PreguntaForm(forms.ModelForm):
    class Meta:
        model = Pregunta
        fields = ['cuestionario', 'texto', 'tipo', 'categoria', 'orden']
        widgets = {
            'texto': forms.Textarea(attrs={'rows': 2}),
        }


class PreguntaFormSet(forms.BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if kwargs.get('instance'):
            self.queryset = Pregunta.objects.filter(
                cuestionario=kwargs['instance']).order_by('orden')


# Cambiamos extra=3 a extra=0 para que no aparezcan formularios vacíos por defecto
PreguntaInlineFormSet = forms.inlineformset_factory(
    Cuestionario, Pregunta, form=PreguntaForm, formset=PreguntaFormSet,
    extra=0, can_delete=True
)


class DiagnosticoForm(forms.ModelForm):
    class Meta:
        model = Diagnostico
        fields = ['departamento', 'cuestionario', 'observaciones']
        widgets = {
            'observaciones': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['cuestionario'].queryset = Cuestionario.objects.filter(
            activo=True)


class RespuestaForm(forms.ModelForm):
    class Meta:
        model = Respuesta
        fields = ['valor_numerico', 'valor_texto']

    def __init__(self, *args, **kwargs):
        pregunta = kwargs.pop('pregunta', None)
        super().__init__(*args, **kwargs)

        if pregunta:
            if pregunta.tipo == 'escala':
                self.fields['valor_numerico'] = forms.ChoiceField(
                    choices=[(i, i) for i in range(1, 6)],
                    widget=forms.RadioSelect,
                    label=pregunta.texto
                )
                self.fields['valor_texto'].widget = forms.HiddenInput()
            elif pregunta.tipo == 'si_no':
                self.fields['valor_numerico'] = forms.ChoiceField(
                    choices=[(1, 'No'), (5, 'Sí')],
                    widget=forms.RadioSelect,
                    label=pregunta.texto
                )
                self.fields['valor_texto'].widget = forms.HiddenInput()
            elif pregunta.tipo == 'texto':
                self.fields['valor_texto'].label = pregunta.texto
                self.fields['valor_numerico'].widget = forms.HiddenInput()
