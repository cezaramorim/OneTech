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
            'codigo', 'nome', 'descricao', 'categoria', 'unidade_medida_interna',
            'preco_custo', 'preco_venda', 'preco_medio',
            'estoque_total', 'quantidade_saidas', 'estoque_atual',
            'controla_estoque', 'ativo', 'data_cadastro',
            'observacoes',
            'fornecedor',
        ]
        labels = {
            'codigo': 'Cód. Fornecedor',
        }
        widgets = {
            'codigo': forms.TextInput(attrs={'class': 'form-control'}),
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            'unidade_medida_interna': forms.Select(attrs={'class': 'form-select'}),
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
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # ✅ Exibe a data formatada dd/mm/yyyy
        if self.instance.pk and self.instance.data_cadastro:
            self.fields['data_cadastro'].initial = self.instance.data_cadastro.strftime('%d/%m/%Y')

        # Remove o prefixo "AUTO-" do código, se existir
        if self.instance.pk and self.instance.codigo and self.instance.codigo.startswith('AUTO-'):
            self.fields['codigo'].initial = self.instance.codigo.replace('AUTO-', '')

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
        widgets = {
            'cst_icms': forms.TextInput(attrs={'class': 'form-control'}),
            'origem_mercadoria': forms.TextInput(attrs={'class': 'form-control'}),
            'aliquota_icms_interna': CurrencyInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'aliquota_icms_interestadual': CurrencyInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'reducao_base_icms': CurrencyInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'cst_ipi': forms.TextInput(attrs={'class': 'form-control'}),
            'aliquota_ipi': CurrencyInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'cst_pis': forms.TextInput(attrs={'class': 'form-control'}),
            'aliquota_pis': CurrencyInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'cst_cofins': forms.TextInput(attrs={'class': 'form-control'}),
            'aliquota_cofins': CurrencyInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'cest': forms.TextInput(attrs={'class': 'form-control'}),
            'ncm': forms.Select(attrs={'class': 'form-select'}), # Adicionado NCM
            'cfop': forms.TextInput(attrs={'class': 'form-control'}), # Adicionado CFOP
            'valor_unitario_comercial': QuantityInput(attrs={'class': 'form-control', 'step': '0.0000000001'}),
            'icms': CurrencyInput(attrs={'class': 'form-control', 'step': '0.0001'}),
            'ipi': CurrencyInput(attrs={'class': 'form-control', 'step': '0.0001'}),
            'pis': CurrencyInput(attrs={'class': 'form-control', 'step': '0.0001'}),
            'cofins': CurrencyInput(attrs={'class': 'form-control', 'step': '0.0001'}),
            'unidade_comercial': forms.TextInput(attrs={'class': 'form-control'}),
            'quantidade_comercial': QuantityInput(attrs={'class': 'form-control', 'step': '0.0001'}),
            'codigo_produto_fornecedor': forms.TextInput(attrs={'class': 'form-control'}),
        }
