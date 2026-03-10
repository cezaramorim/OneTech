# nota_fiscal/forms.py

from django import forms
from django.apps import apps
from django.forms import inlineformset_factory
from .models import NotaFiscal, ItemNotaFiscal, DuplicataNotaFiscal, TransporteNotaFiscal
from produto.ncm_utils import normalizar_codigo_ncm


class NotaFiscalForm(forms.ModelForm):
    class Meta:
        model = NotaFiscal
        fields = [
            'numero',
            'emitente_proprio',
            'destinatario',
            'tipo_operacao',
            'finalidade_emissao',
            'data_emissao',
            'data_saida',
            'natureza_operacao',
            'condicao_pagamento',
            'quantidade_parcelas',
            'valor_total_desconto',
            'valor_total_nota',
            'informacoes_adicionais',
        ]
        labels = {
            'numero': 'Nota Fiscal',
            'emitente_proprio': 'Emitente',
            'destinatario': 'Destinatario',
            'tipo_operacao': 'Tipo de Operacao',
            'finalidade_emissao': 'Finalidade da Emissao',
            'data_emissao': 'Data de Emissao',
            'data_saida': 'Data de Saida/Entrada',
            'natureza_operacao': 'Natureza da Operacao',
            'valor_total_nota': 'Valor Total da Nota',
            'informacoes_adicionais': 'Informacoes Adicionais',
        }
        widgets = {
            'emitente_proprio': forms.Select(attrs={'class': 'form-select'}),
            'destinatario': forms.Select(attrs={'class': 'form-select'}),
            'tipo_operacao': forms.Select(attrs={'class': 'form-select'}),
            'finalidade_emissao': forms.Select(attrs={'class': 'form-select'}),
            'data_emissao': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'data_saida': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'quantidade_parcelas': forms.NumberInput(attrs={'min': 1, 'step': 1}),
            'valor_total_desconto': forms.NumberInput(attrs={'step': '0.01'}),
            'informacoes_adicionais': forms.Textarea(attrs={'rows': 3}),
        }


class ItemNotaFiscalForm(forms.ModelForm):
    class Meta:
        model = ItemNotaFiscal
        fields = ['codigo', 'descricao', 'ncm', 'cfop', 'unidade', 'quantidade', 'valor_unitario', 'valor_total', 'desconto']

    def clean_ncm(self):
        return normalizar_codigo_ncm(self.cleaned_data.get('ncm')) or None


class DuplicataNotaFiscalForm(forms.ModelForm):
    class Meta:
        model = DuplicataNotaFiscal
        fields = ['numero', 'vencimento', 'valor']
        widgets = {
            'vencimento': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
        }


class TransporteNotaFiscalForm(forms.ModelForm):
    class Meta:
        model = TransporteNotaFiscal
        fields = ['modalidade_frete', 'transportadora_nome', 'transportadora_cnpj', 'placa_veiculo', 'uf_veiculo', 'quantidade_volumes', 'peso_liquido', 'peso_bruto']


ItemNotaFiscalFormSet = inlineformset_factory(
    NotaFiscal,
    ItemNotaFiscal,
    form=ItemNotaFiscalForm,
    extra=1,
    can_delete=True,
    fk_name='nota_fiscal'
)

DuplicataNotaFiscalFormSet = inlineformset_factory(
    NotaFiscal,
    DuplicataNotaFiscal,
    form=DuplicataNotaFiscalForm,
    extra=1,
    can_delete=True,
    fk_name='nota_fiscal'
)

TransporteNotaFiscalFormSet = inlineformset_factory(
    NotaFiscal,
    TransporteNotaFiscal,
    form=TransporteNotaFiscalForm,
    extra=0,
    can_delete=False,
    fk_name='nota_fiscal'
)


from control.models import Emitente
from empresas.models import Empresa


class EmpresaDestinatarioSelect(forms.Select):
    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(name, value, label, selected, index, subindex=subindex, attrs=attrs)
        if value:
            try:
                empresa = getattr(value, 'instance', None)
                if not empresa:
                    empresa = self.choices.queryset.filter(pk=value).only('razao_social', 'nome', 'nome_fantasia', 'cnpj', 'cpf').first()
                if not empresa:
                    return option
                tokens = [
                    empresa.razao_social or "",
                    empresa.nome or "",
                    empresa.nome_fantasia or "",
                    empresa.cnpj or "",
                    empresa.cpf or "",
                ]
                option.setdefault('attrs', {})
                option['attrs']['data-search'] = " ".join(tokens).strip().lower()
            except Exception:
                pass
        return option


class CondicaoPagamentoSelect(forms.Select):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.condicoes_map = {}

    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(name, value, label, selected, index, subindex=subindex, attrs=attrs)
        if value in (None, '', 0, '0'):
            return option

        condicao = self.condicoes_map.get(str(value))
        if not condicao:
            return option

        option.setdefault('attrs', {})
        option['attrs']['data-parcelas'] = str(condicao.quantidade_parcelas or 1)
        option['attrs']['data-descricao'] = (condicao.descricao or '').strip()
        return option


class NotaFiscalSaidaForm(forms.ModelForm):
    emitente_proprio = forms.TypedChoiceField(
        choices=(),
        coerce=int,
        empty_value=None,
        label='Nosso Emitente (Matriz/Filial)',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    destinatario = forms.ModelChoiceField(
        queryset=Empresa.objects.all(),
        label='Destinatario (Cliente)',
        widget=EmpresaDestinatarioSelect(attrs={'class': 'form-select'})
    )

    condicao_pagamento_cadastro = forms.ChoiceField(
        choices=(('', 'Selecione'),),
        required=False,
        label='Condicao de Pagamento (Tabela Comercial)',
        widget=CondicaoPagamentoSelect(attrs={'class': 'form-select'})
    )

    class Meta:
        model = NotaFiscal
        fields = [
            'emitente_proprio',
            'destinatario',
            'natureza_operacao',
            'tipo_operacao',
            'finalidade_emissao',
            'condicao_pagamento',
            'quantidade_parcelas',
            'data_emissao',
            'data_saida',
            'informacoes_adicionais',
        ]
        widgets = {
            'natureza_operacao': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo_operacao': forms.Select(attrs={'class': 'form-select'}),
            'finalidade_emissao': forms.Select(attrs={'class': 'form-select'}),
            'condicao_pagamento': forms.HiddenInput(),
            'quantidade_parcelas': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'step': 1}),
            'data_emissao': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}, format='%Y-%m-%d'),
            'data_saida': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}, format='%Y-%m-%d'),
            'informacoes_adicionais': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        emitentes = Emitente.objects.all().only('id', 'razao_social', 'cnpj')
        self.fields['emitente_proprio'].choices = [
            ('', '---------'),
            *[(emitente.id, f"{(emitente.razao_social or '').strip()} ({(emitente.cnpj or '').strip()})" if (emitente.cnpj or '').strip() else (emitente.razao_social or f"Emitente #{emitente.id}")) for emitente in emitentes]
        ]

        default_emitente = Emitente.objects.filter(is_default=True).first()
        if default_emitente:
            self.fields['emitente_proprio'].initial = default_emitente.id

        self.fields['tipo_operacao'].initial = '1'
        self.fields['tipo_operacao'].widget.attrs['readonly'] = True
        self.fields['destinatario'].label_from_instance = (
            lambda empresa: empresa.razao_social or empresa.nome or 'Empresa'
        )

        self._condicoes_pagamento_map = {}
        try:
            CondicaoPagamento = apps.get_model('comercial', 'CondicaoPagamento')
            condicoes = CondicaoPagamento.objects.all().only('id', 'codigo', 'descricao', 'quantidade_parcelas')
            self.fields['condicao_pagamento_cadastro'].choices = [
                ('', 'Selecione a condicao de pagamento'),
                *[(str(condicao.id), f"{condicao.codigo} - {condicao.descricao}") for condicao in condicoes]
            ]
            self._condicoes_pagamento_map = {str(condicao.id): condicao for condicao in condicoes}
            self.fields['condicao_pagamento_cadastro'].widget.condicoes_map = self._condicoes_pagamento_map
        except LookupError:
            self.fields['condicao_pagamento_cadastro'].choices = [('', 'Modulo Comercial nao disponivel')]

    def clean(self):
        cleaned_data = super().clean()
        condicao_id = (cleaned_data.get('condicao_pagamento_cadastro') or '').strip()

        if condicao_id and condicao_id in self._condicoes_pagamento_map:
            condicao = self._condicoes_pagamento_map[condicao_id]
            cleaned_data['condicao_pagamento'] = condicao.descricao
            cleaned_data['quantidade_parcelas'] = condicao.quantidade_parcelas
        elif not cleaned_data.get('quantidade_parcelas'):
            cleaned_data['quantidade_parcelas'] = 1

        return cleaned_data

    def _post_clean(self):
        emitente_id = self.cleaned_data.get('emitente_proprio') if hasattr(self, 'cleaned_data') else None
        if hasattr(self, 'cleaned_data') and 'emitente_proprio' in self.cleaned_data:
            self.cleaned_data['emitente_proprio'] = None
        super()._post_clean()
        if emitente_id:
            self.instance.emitente_proprio_id = emitente_id
