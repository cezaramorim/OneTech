from django import forms
from nota_fiscal.models import NotaFiscal

class NotaFiscalForm(forms.ModelForm):
    class Meta:
        model = NotaFiscal
        fields = [
            'numero',
            'fornecedor',
            'data_emissao',
            'data_saida',
            'valor_total_produtos',
            'valor_total_nota',
            'valor_total_icms',
            'valor_total_pis',
            'valor_total_cofins',
            'valor_total_desconto',
            'informacoes_adicionais',
        ]
        widgets = {
            'data_emissao': forms.DateInput(attrs={'type': 'date'}),
            'data_saida':   forms.DateInput(attrs={'type': 'date'}),
        }
