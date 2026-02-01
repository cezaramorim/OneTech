from django import forms
from django.urls import reverse_lazy
from decimal import Decimal
from .models import Produto, CategoriaProduto, UnidadeMedida, NCM
from .models_fiscais import DetalhesFiscaisProduto

class CurrencyInput(forms.NumberInput):
    def format_value(self, value):
        if isinstance(value, Decimal):
            return f"{value:.2f}"
        return super().format_value(value)

class QuantityInput(forms.NumberInput):
    def format_value(self, value):
        if isinstance(value, Decimal):
            return f"{value:f}"
        return super().format_value(value)

class ProdutoForm(forms.ModelForm):
    class Meta:
        model = Produto
        fields = [
            'codigo_fornecedor', 'nome', 'categoria', 'unidade_medida_interna', 'fator_conversao',
            'preco_custo', 'preco_venda', 'preco_medio',
            'estoque_total', 'quantidade_saidas', 'estoque_atual',
            'controla_estoque', 'ativo', 'data_cadastro',
            'observacoes',
            'fornecedor',
            'unidade_fornecedor_padrao',
        ]
        labels = {
            'codigo_fornecedor': 'Cód. Fornecedor',
        }
        widgets = {
            'codigo_fornecedor': forms.TextInput(attrs={'class': 'form-control'}),
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            'unidade_medida_interna': forms.Select(attrs={'class': 'form-select'}),
            'fator_conversao': QuantityInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 12 para converter de CX para UN'}),
            'cfop': forms.TextInput(attrs={'class': 'form-control'}),
            'preco_custo': CurrencyInput(attrs={'class': 'form-control'}),
            'preco_venda': CurrencyInput(attrs={'class': 'form-control'}),
            'preco_medio': CurrencyInput(attrs={'class': 'form-control', 'readonly': True}),
            'estoque_total': QuantityInput(attrs={'class': 'form-control'}),
            'quantidade_saidas': QuantityInput(attrs={'class': 'form-control'}),
            'estoque_atual': QuantityInput(attrs={'class': 'form-control'}),
            'controla_estoque': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'fornecedor': forms.Select(attrs={'class': 'form-select'}),
            'unidade_fornecedor_padrao': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # ✅ Exibe a data formatada dd/mm/yyyy
        if self.instance.pk and self.instance.data_cadastro:
            self.fields['data_cadastro'].initial = self.instance.data_cadastro.strftime('%d/%m/%Y')

        # ✅ Corrige filtro do fornecedor
        self.fields['fornecedor'].queryset = self.fields['fornecedor'].queryset.filter(tipo_empresa__in=["Fornecedor", "Ambos"], status_empresa=True)

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

class DetalhesFiscaisProdutoForm(forms.ModelForm):
    class Meta:
        model = DetalhesFiscaisProduto
        fields = '__all__'
        exclude = ['produto'] # O produto será associado na view