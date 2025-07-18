from django import forms
from nota_fiscal.models import NotaFiscal

class NotaFiscalForm(forms.ModelForm):
    class Meta:
        model = NotaFiscal
        fields = [
            'numero',
            'emitente',
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
            'data_emissao': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'data_saida': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),

            'valor_total_produtos': forms.NumberInput(attrs={'step': '0000000.000001', 'min': '0'}),
            'valor_total_nota': forms.NumberInput(attrs={'step': '0.0000001', 'min': '0'}),
            'valor_total_icms': forms.NumberInput(attrs={'step': '0.0000001', 'min': '0'}),
            'valor_total_pis': forms.NumberInput(attrs={'step': '0.0000001', 'min': '0'}),
            'valor_total_cofins': forms.NumberInput(attrs={'step': '0.0000001', 'min': '0'}),
            'valor_total_desconto': forms.NumberInput(attrs={'step': '0.000001', 'min': '0'}),
        }
