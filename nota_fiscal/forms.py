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


# Formsets para editar os modelos relacionados na mesma página da Nota Fiscal
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

# Transporte geralmente é um por nota, então não permitimos adicionar/remover, apenas editar.
TransporteNotaFiscalFormSet = inlineformset_factory(
    NotaFiscal, 
    TransporteNotaFiscal, 
    form=TransporteNotaFiscalForm, 
    extra=0, 
    can_delete=False,
    fk_name='nota_fiscal'
)
