from django import forms
from decimal import Decimal # Importar Decimal para o campo rendimento_perc
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

class ImportarCurvaForm(forms.Form):
    nome = forms.CharField(max_length=255, label="Nome da Curva")
    especie = forms.CharField(max_length=100, label="Espécie")
    rendimento_perc = forms.DecimalField(max_digits=5, decimal_places=2, label="% Rendimento")
    arquivo_excel = forms.FileField(label="Arquivo Excel da Curva")

class ExcelUploadForm(forms.Form):
    TIPO_DADO_CHOICES = [
        ('curva_crescimento', 'Curva de Crescimento'),
        ('tanque', 'Tanque'),
    ]
    arquivo_excel = forms.FileField(label="Selecione o arquivo Excel")
    tipo_dado = forms.ChoiceField(label="Tipo de Dado", choices=TIPO_DADO_CHOICES)