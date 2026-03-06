# nota_fiscal/forms.py

from django import forms
from django.forms import inlineformset_factory
from .models import NotaFiscal, ItemNotaFiscal, DuplicataNotaFiscal, TransporteNotaFiscal

class NotaFiscalForm(forms.ModelForm):
    class Meta:
        model = NotaFiscal
        fields = [
            'numero', 'data_emissao', 'data_saida', 'natureza_operacao',
            'valor_total_nota', 'informacoes_adicionais'
        ]
        labels = {
            'numero': 'Nota Fiscal',
        }
        widgets = {
            'data_emissao': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'data_saida': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'informacoes_adicionais': forms.Textarea(attrs={'rows': 3}),
        }

class ItemNotaFiscalForm(forms.ModelForm):
    class Meta:
        model = ItemNotaFiscal
        fields = ['produto', 'codigo', 'descricao', 'ncm', 'cfop', 'unidade', 'quantidade', 'valor_unitario', 'valor_total', 'desconto']

class DuplicataNotaFiscalForm(forms.ModelForm):
    class Meta:
        model = DuplicataNotaFiscal
        fields = ['numero', 'vencimento', 'valor']
        widgets = {
            'vencimento': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
        }

class TransporteNotaFiscalForm(forms.ModelForm):
    class Meta:
        model = TransporteNotaFiscal
        fields = ['modalidade_frete', 'transportadora_nome', 'transportadora_cnpj', 'placa_veiculo', 'uf_veiculo', 'quantidade_volumes', 'peso_liquido', 'peso_bruto']


# Formsets para editar os modelos relacionados na mesma pÃ¡gina da Nota Fiscal
ItemNotaFiscalFormSet = inlineformset_factory(
    NotaFiscal, 
    ItemNotaFiscal, 
    form=ItemNotaFiscalForm, 
    extra=1,  # Permite adicionar novas linhas
    can_delete=True, # Permite remover itens
    fk_name='nota_fiscal'
)

DuplicataNotaFiscalFormSet = inlineformset_factory(
    NotaFiscal, 
    DuplicataNotaFiscal, 
    form=DuplicataNotaFiscalForm, 
    extra=1, 
    can_delete=True,
    fk_name='nota_fiscal'
)

# Transporte geralmente Ã© um por nota, entÃ£o nÃ£o permitimos adicionar/remover, apenas editar.
TransporteNotaFiscalFormSet = inlineformset_factory(
    NotaFiscal, 
    TransporteNotaFiscal, 
    form=TransporteNotaFiscalForm, 
    extra=0, 
    can_delete=False,
    fk_name='nota_fiscal'
)

# ==============================================================================
# ðŸš€ FORMULÃRIO PARA NOTA FISCAL DE SAÃDA
# ==============================================================================
from control.models import Emitente
from empresas.models import Empresa

class NotaFiscalSaidaForm(forms.ModelForm):
    emitente_proprio = forms.ModelChoiceField(
        queryset=Emitente.objects.all(),
        label="Nosso Emitente (Matriz/Filial)",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    destinatario = forms.ModelChoiceField(
        queryset=Empresa.objects.filter(cliente=True),
        label="DestinatÃ¡rio (Cliente)",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = NotaFiscal
        fields = [
            'emitente_proprio',
            'destinatario',
            'natureza_operacao',
            'tipo_operacao',
            'finalidade_emissao',
            'data_emissao',
            'data_saida',
            'informacoes_adicionais',
        ]
        widgets = {
            'natureza_operacao': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo_operacao': forms.Select(attrs={'class': 'form-select'}),
            'finalidade_emissao': forms.Select(attrs={'class': 'form-select'}),
            'data_emissao': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}, format='%Y-%m-%d'),
            'data_saida': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}, format='%Y-%m-%d'),
            'informacoes_adicionais': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Tenta prÃ©-selecionar o emitente padrÃ£o
        default_emitente = Emitente.objects.filter(is_default=True).first()
        if default_emitente:
            self.fields['emitente_proprio'].initial = default_emitente
        
        # Define o tipo de operaÃ§Ã£o como 'SaÃ­da' por padrÃ£o e o torna somente leitura
        self.fields['tipo_operacao'].initial = '1' # '1' para SaÃ­da
        self.fields['tipo_operacao'].widget.attrs['readonly'] = True
