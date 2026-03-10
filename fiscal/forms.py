from django import forms
from .models import Cfop, NaturezaOperacao


class CfopForm(forms.ModelForm):
    class Meta:
        model = Cfop
        fields = ['codigo', 'descricao', 'categoria']
        widgets = {
            'codigo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 5102'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Descri\u00e7\u00e3o completa do CFOP'}),
            'categoria': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Entrada, Sa\u00edda'}),
        }


class NaturezaOperacaoForm(forms.ModelForm):
    class Meta:
        model = NaturezaOperacao
        fields = ['codigo', 'descricao', 'observacoes']
        widgets = {
            'codigo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: VENDA'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Descri\u00e7\u00e3o da natureza de opera\u00e7\u00e3o'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Observa\u00e7\u00f5es adicionais (opcional)'}),
        }


class UploadExcelForm(forms.Form):
    excel_file = forms.FileField(label='Arquivo Excel')
    import_type = forms.ChoiceField(
        label='Tipo de Importa\u00e7\u00e3o',
        choices=[('cfop', 'CFOP'), ('natureza_operacao', 'Natureza de Opera\u00e7\u00e3o')],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
