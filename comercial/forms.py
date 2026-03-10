from django import forms

from .models import CondicaoPagamento


class CondicaoPagamentoForm(forms.ModelForm):
    codigo = forms.CharField(
        label='Codigo',
        required=False,
        disabled=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'})
    )

    class Meta:
        model = CondicaoPagamento
        fields = ['descricao', 'quantidade_parcelas', 'observacoes']
        widgets = {
            'descricao': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Descricao da condicao de pagamento'}),
            'quantidade_parcelas': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'step': 1}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Ex.: 0 | 7 | 14 | 21/28/35'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['codigo'].initial = self.instance.codigo if self.instance and self.instance.pk else 'Automatico'
        self.fields['observacoes'].label = 'Dias de vencimento'
        self.fields['observacoes'].help_text = (
            'Informe os dias apos a emissao, separados por / quando houver mais de uma parcela. '
            'Ex.: 0, 7, 14, 21/28/35.'
        )
        self.fields['quantidade_parcelas'].help_text = (
            'Informe a quantidade de vencimentos. Ex.: 21/28/35 = 3 parcelas.'
        )
        self.order_fields(['codigo', 'descricao', 'quantidade_parcelas', 'observacoes'])
