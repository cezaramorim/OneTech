from django import forms
from .models import Cfop, NaturezaOperacao

class CfopForm(forms.ModelForm):
    class Meta:
        model = Cfop
        fields = ['codigo', 'descricao', 'categoria']
        widgets = {
            'codigo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 5102'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Descrição completa do CFOP'}),
            'categoria': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Entrada, Saída'}),
        }

class NaturezaOperacaoForm(forms.ModelForm):
    class Meta:
        model = NaturezaOperacao
        fields = ['codigo', 'descricao', 'observacoes']
        widgets = {
            'codigo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: VENDA'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Descrição da natureza de operação'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Observações adicionais (opcional)'}),
        }

class UploadExcelForm(forms.Form):
    excel_file = forms.FileField(label='Arquivo Excel')
    import_type = forms.ChoiceField(
        label='Tipo de Importação',
        choices=[('cfop', 'CFOP'), ('natureza_operacao', 'Natureza de Operação')],
        widget=forms.Select(attrs={'class': 'form-control'})
    )