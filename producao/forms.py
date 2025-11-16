from django import forms
from django.core.exceptions import ValidationError
from decimal import Decimal
from .models import (
    Tanque, CurvaCrescimento, CurvaCrescimentoDetalhe, Lote, EventoManejo,
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
        widget=forms.Select(attrs={'class': 'form-control form-control-sm'}),
        label="Ativo"
    )

    class Meta:
        model = Tanque
        fields = [ # Lista explícita para melhor controle da ordem
            'nome',
            'unidade', 'linha_producao', 'fase', 'tipo_tanque',
            'status_tanque',
            'sequencia',
            'largura', 'comprimento', 'profundidade',
            'malha', 'ativo',
            'tipo_tela',
            'tag_tanque',
        ]
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'sequencia': forms.NumberInput(attrs={'class': 'form-control form-control-sm'}),
            'tag_tanque': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'largura': forms.TextInput(attrs={'class': 'form-control form-control-sm', 'inputmode': 'decimal'}),
            'comprimento': forms.TextInput(attrs={'class': 'form-control form-control-sm', 'inputmode': 'decimal'}),
            'profundidade': forms.TextInput(attrs={'class': 'form-control form-control-sm', 'inputmode': 'decimal'}),
            'unidade': forms.Select(attrs={'class': 'form-control form-control-sm'}),
            'fase': forms.Select(attrs={'class': 'form-control form-control-sm'}),
            'tipo_tanque': forms.Select(attrs={'class': 'form-control form-control-sm'}),
            'linha_producao': forms.Select(attrs={'class': 'form-control form-control-sm'}),
            'malha': forms.Select(attrs={'class': 'form-control form-control-sm'}),
            'status_tanque': forms.Select(attrs={'class': 'form-control form-control-sm'}),
            'tipo_tela': forms.Select(attrs={'class': 'form-control form-control-sm'}),
        }

# --- Formulário de Importação ---

class TanqueImportForm(forms.Form):
    arquivo_excel = forms.FileField(label="Selecione o arquivo Excel para importar tanques")


# --- Formulários de Negócio com Validações Aprimoradas ---

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

    def clean(self):
        cleaned_data = super().clean()
        for field_name in ['quantidade_inicial', 'peso_medio_inicial', 'quantidade_atual', 'peso_medio_atual']:
            if cleaned_data.get(field_name) is not None and cleaned_data.get(field_name) < 0:
                self.add_error(field_name, "Este valor não pode ser negativo.")
        return cleaned_data

class EventoManejoForm(forms.ModelForm):
    class Meta:
        model = EventoManejo
        fields = '__all__'
        labels = {
            'quantidade': 'Qtde',
            'peso_medio': 'P.Médio(g)',
        }

    def clean(self):
        cleaned_data = super().clean()
        for field_name in ['quantidade', 'peso_medio']:
            if cleaned_data.get(field_name) is not None and cleaned_data.get(field_name) < 0:
                self.add_error(field_name, "Este valor não pode ser negativo.")
        return cleaned_data

class CurvaCrescimentoDetalheForm(forms.ModelForm):
    class Meta:
        model = CurvaCrescimentoDetalhe
        fields = '__all__'
        exclude = ['curva']

    def clean_arracoamento_biomassa_perc(self):
        """Valida se o %BW/dia está em um range aceitável."""
        percentual = self.cleaned_data.get('arracoamento_biomassa_perc')
        if percentual is not None and not (Decimal('0') <= percentual <= Decimal('20')):
            raise ValidationError("O percentual de arraçoamento deve estar entre 0 e 20%.")
        return percentual

    def clean(self):
        """Valida a sobreposição de faixas de peso."""
        cleaned_data = super().clean()
        peso_inicial = cleaned_data.get('peso_inicial')
        peso_final = cleaned_data.get('peso_final')
        curva = self.instance.curva # A curva é associada na view antes de validar

        if peso_inicial is not None and peso_final is not None:
            if peso_inicial >= peso_final:
                self.add_error('peso_final', "O peso final deve ser maior que o peso inicial.")
                return cleaned_data

            # Verifica sobreposição com outros detalhes da mesma curva
            qs = CurvaCrescimentoDetalhe.objects.filter(curva=curva)
            if self.instance.pk: # Se for edição, exclui o próprio objeto da verificação
                qs = qs.exclude(pk=self.instance.pk)
            
            for detalhe in qs:
                # Verifica se a nova faixa (A) sobrepõe uma faixa existente (B)
                # Condição: (A.inicio < B.fim) e (A.fim > B.inicio)
                if (peso_inicial < detalhe.peso_final) and (peso_final > detalhe.peso_inicial):
                    raise ValidationError(
                        f"A faixa de peso ({peso_inicial}g - {peso_final}g) sobrepõe uma faixa existente "
                        f"({detalhe.peso_inicial}g - {detalhe.peso_final}g) para esta curva."
                    )
        return cleaned_data


# --- Formulários de Importação e Ações ---

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

TIPO_TANQUE_CHOICES = [
    ('VAZIO', 'Tanque Vazio'),
    ('POVOADO', 'Tanque Povoado'),
]

class PovoamentoForm(forms.Form):
    tipo_tanque = forms.ChoiceField(choices=TIPO_TANQUE_CHOICES)
    curva_id = forms.IntegerField(required=False)
    tanque_id = forms.IntegerField()
    grupo_origem = forms.CharField()
    data_lancamento = forms.DateField(input_formats=['%Y-%m-%d'])
    nome_lote = forms.CharField(max_length=255, required=False)
    quantidade = forms.DecimalField(min_value=Decimal('0.01'), max_digits=10, decimal_places=2)
    peso_medio = forms.DecimalField(min_value=Decimal('0.01'), max_digits=10, decimal_places=3)
    fase_id = forms.IntegerField()
    tamanho = forms.CharField(required=False)
    linha_id = forms.IntegerField()

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("tipo_tanque") == "Tanque Vazio":
            if not cleaned_data.get("nome_lote"):
                self.add_error("nome_lote", "O campo 'Nome Lote' é obrigatório.")
            if not cleaned_data.get("curva_id"):
                self.add_error("curva_id", "O campo 'Curva de Crescimento' é obrigatório.")
        return cleaned_data
