from django import forms
from .models import Cfop, NaturezaOperacao


class CfopForm(forms.ModelForm):
    class Meta:
        model = Cfop
        fields = ['codigo', 'descricao', 'categoria']
        widgets = {
            'codigo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 5102'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Descricao completa do CFOP'}),
            'categoria': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Entrada, Saida'}),
        }


class NaturezaOperacaoForm(forms.ModelForm):
    class Meta:
        model = NaturezaOperacao
        fields = ['codigo', 'descricao', 'observacoes']
        widgets = {
            'codigo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: VENDA'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Descricao da natureza de operacao'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Observacoes adicionais (opcional)'}),
        }


class UploadExcelForm(forms.Form):
    excel_file = forms.FileField(label='Arquivo Excel')
    import_type = forms.ChoiceField(
        label='Tipo de Importacao',
        choices=[
            ('cfop', 'CFOP'),
            ('natureza_operacao', 'Natureza de Operacao'),
            ('icms_origem_destino', 'ICMS Origem x Destino'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
