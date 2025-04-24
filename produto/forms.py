from django import forms
from django.urls import reverse_lazy
from .models import Produto, CategoriaProduto, UnidadeMedida, NCM


class ProdutoForm(forms.ModelForm):
    # Campo auxiliar de texto para busca dinâmica por NCM
    ncm_descricao = forms.CharField(
        label="NCM",
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'id': 'ncm-busca-produto',
            'placeholder': 'Buscar por código ou descrição do NCM',
            'autocomplete': 'off',
        })
    )

    class Meta:
        model = Produto
        fields = [
            'codigo', 'nome', 'descricao', 'categoria', 'unidade_medida',
            'cfop', 'preco_custo', 'preco_venda', 'preco_medio',
            'estoque_total', 'quantidade_saidas', 'estoque_atual',
            'controla_estoque', 'ativo', 'data_cadastro',
            'observacoes',
            # ❌ 'ncm' removido do formulário visual
        ]
        widgets = {
            'codigo': forms.TextInput(attrs={'class': 'form-control'}),
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            'unidade_medida': forms.Select(attrs={'class': 'form-select'}),
            'cfop': forms.TextInput(attrs={'class': 'form-control'}),
            'preco_custo': forms.NumberInput(attrs={'class': 'form-control'}),
            'preco_venda': forms.NumberInput(attrs={'class': 'form-control'}),
            'preco_medio': forms.NumberInput(attrs={'class': 'form-control', 'readonly': True}),
            'estoque_total': forms.NumberInput(attrs={'class': 'form-control'}),
            'quantidade_saidas': forms.NumberInput(attrs={'class': 'form-control'}),
            'estoque_atual': forms.NumberInput(attrs={'class': 'form-control'}),
            'controla_estoque': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'data_cadastro': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Exibe o NCM atual no campo auxiliar em caso de edição
        if self.instance.pk and self.instance.ncm:
            ncm_obj = self.instance.ncm
            self.fields['ncm_descricao'].initial = f"{ncm_obj.codigo} - {ncm_obj.descricao}"

    def clean(self):
        cleaned_data = super().clean()
        termo = cleaned_data.get('ncm_descricao', '').strip()

        if termo:
            codigo = termo.split(' ')[0]  # pega o código do NCM
            try:
                ncm = NCM.objects.get(codigo=codigo)
                cleaned_data['ncm'] = ncm
            except NCM.DoesNotExist:
                self.add_error('ncm_descricao', 'NCM não encontrado.')
        else:
            cleaned_data['ncm'] = None

        return cleaned_data

class CategoriaProdutoForm(forms.ModelForm):
    class Meta:
        model = CategoriaProduto
        fields = '__all__'
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'descricao': forms.TextInput(attrs={'class': 'form-control'}),
        }


class UnidadeMedidaForm(forms.ModelForm):
    class Meta:
        model = UnidadeMedida
        fields = '__all__'
        widgets = {
            'sigla': forms.TextInput(attrs={'class': 'form-control'}),
            'descricao': forms.TextInput(attrs={'class': 'form-control'}),
        }
