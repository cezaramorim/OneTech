from django import forms

from .models import RegraAliquotaICMS


class RegraAliquotaICMSForm(forms.ModelForm):
    class Meta:
        model = RegraAliquotaICMS
        fields = [
            'ativo',
            'descricao',
            'ncm_prefixo',
            'tipo_operacao',
            'modalidade',
            'uf_origem',
            'uf_destino',
            'origem_mercadoria',
            'cst_icms',
            'csosn_icms',
            'aliquota_icms',
            'fcp',
            'reducao_base_icms',
            'prioridade',
            'vigencia_inicio',
            'vigencia_fim',
            'observacoes',
        ]
        widgets = {
            'descricao': forms.TextInput(attrs={'class': 'form-control'}),
            'ncm_prefixo': forms.TextInput(attrs={'class': 'form-control', 'maxlength': 8}),
            'tipo_operacao': forms.Select(attrs={'class': 'form-select'}),
            'modalidade': forms.Select(attrs={'class': 'form-select'}),
            'uf_origem': forms.TextInput(attrs={'class': 'form-control', 'maxlength': 2}),
            'uf_destino': forms.TextInput(attrs={'class': 'form-control', 'maxlength': 2}),
            'origem_mercadoria': forms.TextInput(attrs={'class': 'form-control', 'maxlength': 1}),
            'cst_icms': forms.Select(attrs={'class': 'form-select'}),
            'csosn_icms': forms.Select(attrs={'class': 'form-select'}),
            'aliquota_icms': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'fcp': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'reducao_base_icms': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'prioridade': forms.NumberInput(attrs={'class': 'form-control'}),
            'vigencia_inicio': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'vigencia_fim': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def clean_uf_origem(self):
        return (self.cleaned_data.get('uf_origem') or '').strip().upper() or None

    def clean_uf_destino(self):
        return (self.cleaned_data.get('uf_destino') or '').strip().upper() or None
