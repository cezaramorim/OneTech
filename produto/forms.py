from django import forms
from django.db.models import Q
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
            'codigo_fornecedor': 'CÃ³d. Fornecedor',
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

        # âœ… Exibe a data formatada dd/mm/yyyy
        if self.instance.pk and self.instance.data_cadastro:
            self.fields['data_cadastro'].initial = self.instance.data_cadastro.strftime('%d/%m/%Y')

        # Fornecedores validos no fluxo atual: ativos, marcados como fornecedor
        # ou ja vinculados a produtos existentes. Em edicao, preserva o fornecedor atual.
        fornecedor_qs = self.fields['fornecedor'].queryset
        fornecedor_atual_id = getattr(self.instance, 'fornecedor_id', None)

        fornecedor_qs = fornecedor_qs.filter(
            Q(status_empresa='ativa') & (
                Q(fornecedor=True)
                | Q(produtos_fornecidos__isnull=False)
                | Q(pk=fornecedor_atual_id)
            )
        ).distinct()

        self.fields['fornecedor'].queryset = fornecedor_qs.order_by('razao_social', 'nome_fantasia', 'nome', 'id')

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
    ncm_busca = forms.CharField(
        required=False,
        label='NCM',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    cfop_busca = forms.CharField(
        required=False,
        label='CFOP',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = DetalhesFiscaisProduto
        fields = '__all__'
        exclude = ['produto'] # O produto serÃ¡ associado na view

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        current_codigo = getattr(getattr(self.instance, 'ncm', None), 'codigo', '') or ''
        submitted_codigo = (self.data.get(self.add_prefix('ncm')) or '').strip() if self.is_bound else ''
        allowed_codigos = [codigo for codigo in [current_codigo, submitted_codigo] if codigo]

        if allowed_codigos:
            self.fields['ncm'].queryset = NCM.objects.filter(codigo__in=allowed_codigos).order_by('codigo')
        else:
            self.fields['ncm'].queryset = NCM.objects.none()

        self.fields['ncm'].to_field_name = 'codigo'
        self.fields['ncm'].widget.attrs.update({
            'class': 'd-none',
            'tabindex': '-1',
            'aria-hidden': 'true',
        })

        self.fields['ncm_busca'].initial = (
            self.instance.ncm.codigo_formatado
            if getattr(self.instance, 'ncm_id', None)
            else ''
        )
        self.fields['ncm_busca'].widget.attrs.update({
            'placeholder': 'Buscar NCM por codigo ou descricao',
            'autocomplete': 'off',
        })


        self.fields['cfop'].widget.attrs.update({
            'class': 'd-none',
            'tabindex': '-1',
            'aria-hidden': 'true',
        })

        self.fields['cfop_busca'].initial = (
            (self.instance.cfop or '').strip()
            if getattr(self.instance, 'pk', None)
            else ''
        )
        self.fields['cfop_busca'].widget.attrs.update({
            'placeholder': 'Buscar CFOP por codigo ou descricao',
            'autocomplete': 'off',
        })

        self.fields['origem_mercadoria'].widget.attrs.update({
            'class': 'form-select select2-origem-mercadoria',
            'data-placeholder': 'Selecione a origem da mercadoria',
        })

    def clean_cfop(self):
        value = (self.cleaned_data.get('cfop') or '').strip()
        if not value:
            value = (self.data.get(self.add_prefix('cfop_busca')) or '').strip()
        digits = ''.join(ch for ch in value if ch.isdigit())[:4]
        return digits or None

