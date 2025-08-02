from django import forms
from decimal import Decimal
from .models import (
    Tanque, CurvaCrescimento, Lote, EventoManejo, AlimentacaoDiaria,
    Unidade, Malha, TipoTela, LinhaProducao, FaseProducao, StatusTanque, TipoTanque, Atividade
)

# --- Formulários de Suporte ---

class UnidadeForm(forms.ModelForm):
    class Meta:
        model = Unidade
        fields = '__all__'

class MalhaForm(forms.ModelForm):
    class Meta:
        model = Malha
        fields = '__all__'

class TipoTelaForm(forms.ModelForm):
    class Meta:
        model = TipoTela
        fields = '__all__'

class LinhaProducaoForm(forms.ModelForm):
    class Meta:
        model = LinhaProducao
        fields = '__all__'

class FaseProducaoForm(forms.ModelForm):
    class Meta:
        model = FaseProducao
        fields = '__all__'

class StatusTanqueForm(forms.ModelForm):
    class Meta:
        model = StatusTanque
        fields = '__all__'

class TipoTanqueForm(forms.ModelForm):
    class Meta:
        model = TipoTanque
        fields = '__all__'

class AtividadeForm(forms.ModelForm):
    class Meta:
        model = Atividade
        fields = '__all__'

# --- Formulário Principal de Tanque ---

class TanqueForm(forms.ModelForm):
    class Meta:
        model = Tanque
        fields = [ # Lista explícita para melhor controle da ordem
            'nome', 'tag_tanque', 'ativo',
            'unidade', 'linha_producao', 'fase', 'tipo_tanque', 
            'status_tanque', 'sequencia',
            'largura', 'comprimento', 'profundidade', 
            'malha', 'tipo_tela',
        ]

# --- Formulário de Importação ---

class TanqueImportForm(forms.Form):
    arquivo_excel = forms.FileField(label="Selecione o arquivo Excel para importar tanques")


# --- Formulários Existentes (sem alteração) ---

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
