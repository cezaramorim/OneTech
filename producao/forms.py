from django import forms
from decimal import Decimal
from .models import (
    Tanque, CurvaCrescimento, CurvaCrescimentoDetalhe, Lote, EventoManejo, AlimentacaoDiaria,
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

ATIVO_CHOICES = [
    (True, 'Sim'),
    (False, 'Não'),
]

class TanqueForm(forms.ModelForm):
    ativo = forms.ChoiceField(
        choices=ATIVO_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Ativo"
    )

    class Meta:
        model = Tanque
        fields = [ # Lista explícita para melhor controle da ordem
            'nome', 'tag_tanque',
            'unidade', 'linha_producao', 'fase', 'tipo_tanque',
            'status_tanque', 'sequencia',
            'largura', 'comprimento', 'profundidade',
            'malha', 'tipo_tela', 'ativo', # 'ativo' moved to explicit field
        ]
        widgets = {
            'largura': forms.TextInput(attrs={
                'class': 'form-control',
                'inputmode': 'decimal',
            }),
            'comprimento': forms.TextInput(attrs={
                'class': 'form-control',
                'inputmode': 'decimal',
            }),
            'profundidade': forms.TextInput(attrs={
                'class': 'form-control',
                'inputmode': 'decimal',
            }),
        }

# --- Formulário de Importação ---

class TanqueImportForm(forms.Form):
    arquivo_excel = forms.FileField(label="Selecione o arquivo Excel para importar tanques")


# --- Formulários Existentes (sem alteração) ---

class CurvaCrescimentoForm(forms.ModelForm):
    class Meta:
        model = CurvaCrescimento
        fields = '__all__'
        widgets = {
            'nome': forms.TextInput(attrs={'id': 'id_nome'}),
            'especie': forms.TextInput(attrs={'id': 'id_especie'}),
            'rendimento_perc': forms.NumberInput(attrs={'id': 'id_rendimento_perc'}),
            'trato_perc_curva': forms.NumberInput(attrs={'id': 'id_trato_perc_curva'}),
            'peso_pretendido': forms.NumberInput(attrs={'id': 'id_peso_pretendido'}),
            'trato_sabados_perc': forms.NumberInput(attrs={'id': 'id_trato_sabados_perc'}),
            'trato_domingos_perc': forms.NumberInput(attrs={'id': 'id_trato_domingos_perc'}),
            'trato_feriados_perc': forms.NumberInput(attrs={'id': 'id_trato_feriados_perc'}),
        }

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

class CurvaCrescimentoDetalheForm(forms.ModelForm):
    class Meta:
        model = CurvaCrescimentoDetalhe
        fields = '__all__'
        exclude = ['curva']  # O campo 'curva' será associado automaticamente na view
        widgets = {
            'periodo_semana': forms.NumberInput(attrs={'id': 'id_periodo_semana'}),
            'periodo_dias': forms.NumberInput(attrs={'id': 'id_periodo_dias'}),
            'peso_inicial': forms.NumberInput(attrs={'id': 'id_peso_inicial'}),
            'peso_final': forms.NumberInput(attrs={'id': 'id_peso_final'}),
            'ganho_de_peso': forms.NumberInput(attrs={'id': 'id_ganho_de_peso'}),
            'numero_tratos': forms.NumberInput(attrs={'id': 'id_numero_tratos'}),
            'hora_inicio': forms.TimeInput(attrs={'id': 'id_hora_inicio'}),
            'arracoamento_biomassa_perc': forms.NumberInput(attrs={'id': 'id_arracoamento_biomassa_perc'}),
            'mortalidade_presumida_perc': forms.NumberInput(attrs={'id': 'id_mortalidade_presumida_perc'}),
            'racao': forms.Select(attrs={'id': 'id_racao'}), # Assuming 'racao' is a ForeignKey, so a Select widget
            'gpd': forms.NumberInput(attrs={'id': 'id_gpd'}),
            'tca': forms.NumberInput(attrs={'id': 'id_tca'}),
        }

