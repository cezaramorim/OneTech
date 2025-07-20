from django import forms
from .models import Tanque, CurvaCrescimento, Lote, EventoManejo, AlimentacaoDiaria

class TanqueForm(forms.ModelForm):
    class Meta:
        model = Tanque
        fields = '__all__'

class CurvaCrescimentoForm(forms.ModelForm):
    class Meta:
        model = CurvaCrescimento
        fields = '__all__'

class LoteForm(forms.ModelForm):
    class Meta:
        model = Lote
        fields = '__all__'

class EventoManejoForm(forms.ModelForm):
    class Meta:
        model = EventoManejo
        fields = '__all__'

class AlimentacaoDiariaForm(forms.ModelForm):
    class Meta:
        model = AlimentacaoDiaria
        fields = '__all__'

class ExcelUploadForm(forms.Form):
    TIPO_DADO_CHOICES = [
        ('curva_crescimento', 'Curva de Crescimento'),
        ('tanque', 'Tanque'),
    ]
    arquivo_excel = forms.FileField(label="Selecione o arquivo Excel")
    tipo_dado = forms.ChoiceField(label="Tipo de Dado", choices=TIPO_DADO_CHOICES)