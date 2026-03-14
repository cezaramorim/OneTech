# nota_fiscal/forms.py

from django import forms
from django.apps import apps
from django.forms import inlineformset_factory
from .models import NotaFiscal, ItemNotaFiscal, DuplicataNotaFiscal, TransporteNotaFiscal
from produto.ncm_utils import normalizar_codigo_ncm
from control.models import Emitente
from empresas.models import Empresa, CategoriaEmpresa


def _ensure_current_value_choice(field, current_value, label_prefix='Atual'):
    current = (current_value or '').strip()
    if not current:
        return
    for value, _label in field.choices:
        if str(value).strip() == current:
            return
    field.choices = list(field.choices) + [(current, f'{label_prefix}: {current}')]
    field.initial = current


class NotaFiscalForm(forms.ModelForm):
    emitente_proprio = forms.TypedChoiceField(
        choices=(),
        coerce=int,
        empty_value=None,
        required=False,
        label='Emitente',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    natureza_operacao = forms.ChoiceField(
        choices=(('', 'Selecione a natureza de operacao'),),
        required=False,
        label='Natureza da Operacao',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    condicao_pagamento = forms.ChoiceField(
        choices=(('', 'Selecione a condicao de pagamento'),),
        required=False,
        label='Condicao de Pagamento',
        widget=forms.Select(attrs={'class': 'form-select'})
    )

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
            'condicao_pagamento': 'Condicao de Pagamento',
            'quantidade_parcelas': 'Quantidade de Parcelas',
            'valor_total_nota': 'Valor Total da Nota',
            'informacoes_adicionais': 'Informacoes Adicionais',
        }
        widgets = {
            'destinatario': forms.Select(attrs={'class': 'form-select'}),
            'tipo_operacao': forms.Select(attrs={'class': 'form-select'}),
            'finalidade_emissao': forms.Select(attrs={'class': 'form-select'}),
            'data_emissao': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'data_saida': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'quantidade_parcelas': forms.NumberInput(attrs={'min': 1, 'step': 1, 'readonly': 'readonly', 'class': 'bg-light'}),
            'valor_total_desconto': forms.NumberInput(attrs={'step': '0.01'}),
            'informacoes_adicionais': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        emitentes = Emitente.objects.all().only('id', 'razao_social', 'cnpj')
        self.fields['emitente_proprio'].choices = [
            ('', '---------'),
            *[
                (
                    emitente.id,
                    f"{(emitente.razao_social or '').strip()} ({(emitente.cnpj or '').strip()})"
                    if (emitente.cnpj or '').strip()
                    else (emitente.razao_social or f"Emitente #{emitente.id}")
                )
                for emitente in emitentes
            ],
        ]
        if self.instance and self.instance.pk:
            self.fields['emitente_proprio'].initial = self.instance.emitente_proprio_id

        self._naturezas_map = {}
        try:
            NaturezaOperacao = apps.get_model('fiscal', 'NaturezaOperacao')
            naturezas = NaturezaOperacao.objects.all().only('id', 'codigo', 'descricao')
            self.fields['natureza_operacao'].choices = [
                ('', 'Selecione a natureza de operacao'),
                *[(str(n.id), f"{(n.codigo or '').strip()} - {(n.descricao or '').strip()}".strip(' -')) for n in naturezas]
            ]
            self._naturezas_map = {str(n.id): n for n in naturezas}

            atual = (self.instance.natureza_operacao or '').strip() if self.instance else ''
            if atual:
                def _norm_nat(value):
                    return ' '.join(str(value or '').strip().lower().split())

                alvo_nat = _norm_nat(atual)
                match = ''
                for n in naturezas:
                    codigo = str(n.codigo or '').strip()
                    descricao = str(n.descricao or '').strip()
                    candidatos = {
                        _norm_nat(descricao),
                        _norm_nat(codigo),
                        _norm_nat(f"{codigo} - {descricao}"),
                    }
                    if alvo_nat in candidatos:
                        match = str(n.id)
                        break

                if match:
                    self.fields['natureza_operacao'].initial = match
                    self.initial['natureza_operacao'] = match
                else:
                    _ensure_current_value_choice(self.fields['natureza_operacao'], atual, label_prefix='Atual (importado)')
        except LookupError:
            self.fields['natureza_operacao'].choices = [('', 'Modulo Fiscal indisponivel')]

        self._condicoes_pagamento_map = {}
        self.fields['condicao_pagamento'].widget = CondicaoPagamentoSelect(attrs={'class': 'form-select'})
        try:
            CondicaoPagamento = apps.get_model('comercial', 'CondicaoPagamento')
            condicoes = CondicaoPagamento.objects.all().only('id', 'codigo', 'descricao', 'quantidade_parcelas', 'observacoes')
            self.fields['condicao_pagamento'].choices = [
                ('', 'Selecione a condicao de pagamento'),
                *[(str(c.id), f"{c.codigo} - {c.descricao}") for c in condicoes]
            ]
            self._condicoes_pagamento_map = {str(c.id): c for c in condicoes}
            self.fields['condicao_pagamento'].widget.condicoes_map = self._condicoes_pagamento_map

            atual = (self.instance.condicao_pagamento or '').strip() if self.instance else ''
            if atual:
                def _norm(value):
                    return ' '.join(str(value or '').strip().lower().split())

                alvo = _norm(atual)
                match = ''
                for c in condicoes:
                    codigo = str(c.codigo or '').strip()
                    descricao = str(c.descricao or '').strip()
                    candidatos = {
                        _norm(descricao),
                        _norm(codigo),
                        _norm(f"{codigo} - {descricao}"),
                    }
                    if alvo in candidatos:
                        match = str(c.id)
                        break

                if match:
                    self.fields['condicao_pagamento'].initial = match
                    self.initial['condicao_pagamento'] = match
                else:
                    _ensure_current_value_choice(self.fields['condicao_pagamento'], atual, label_prefix='Atual (importado)')
        except LookupError:
            self.fields['condicao_pagamento'].choices = [('', 'Modulo Comercial indisponivel')]

        self.fields['quantidade_parcelas'].widget.attrs['readonly'] = True
        self.fields['quantidade_parcelas'].widget.attrs['class'] = f"{self.fields['quantidade_parcelas'].widget.attrs.get('class', '')} bg-light".strip()

    def clean(self):
        cleaned_data = super().clean()

        cleaned_data['tipo_operacao'] = '1'

        natureza_id = (cleaned_data.get('natureza_operacao') or '').strip()
        if natureza_id and natureza_id in self._naturezas_map:
            cleaned_data['natureza_operacao'] = (self._naturezas_map[natureza_id].descricao or '').strip()
        elif self.instance and self.instance.pk:
            cleaned_data['natureza_operacao'] = self.instance.natureza_operacao

        condicao_id = (cleaned_data.get('condicao_pagamento') or '').strip()
        if condicao_id and condicao_id in self._condicoes_pagamento_map:
            condicao = self._condicoes_pagamento_map[condicao_id]
            cleaned_data['condicao_pagamento'] = (condicao.descricao or '').strip()
            cleaned_data['quantidade_parcelas'] = condicao.quantidade_parcelas or 1
        elif self.instance and self.instance.pk and self.instance.condicao_pagamento:
            cleaned_data['condicao_pagamento'] = self.instance.condicao_pagamento
            cleaned_data['quantidade_parcelas'] = self.instance.quantidade_parcelas or 1
        elif not cleaned_data.get('quantidade_parcelas'):
            cleaned_data['quantidade_parcelas'] = 1

        return cleaned_data

    def _post_clean(self):
        emitente_id = self.cleaned_data.get('emitente_proprio') if hasattr(self, 'cleaned_data') else None
        if hasattr(self, 'cleaned_data') and 'emitente_proprio' in self.cleaned_data:
            self.cleaned_data['emitente_proprio'] = None
        super()._post_clean()
        self.instance.emitente_proprio_id = emitente_id or None


class NotaFiscalEntradaForm(forms.ModelForm):
    natureza_operacao = forms.ChoiceField(
        choices=(('', 'Selecione a natureza de operacao'),),
        required=False,
        label='Natureza da Operacao',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    condicao_pagamento = forms.ChoiceField(
        choices=(('', 'Selecione a condicao de pagamento'),),
        required=False,
        label='Condicao de Pagamento',
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = NotaFiscal
        fields = [
            'numero',
            'emitente',
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
            'emitente': 'Fornecedor (Emitente)',
            'destinatario': 'Destinatario',
            'tipo_operacao': 'Tipo de Operacao',
            'finalidade_emissao': 'Finalidade da Emissao',
            'data_emissao': 'Data de Emissao',
            'data_saida': 'Data de Saida/Entrada',
            'natureza_operacao': 'Natureza da Operacao',
            'condicao_pagamento': 'Condicao de Pagamento',
            'quantidade_parcelas': 'Quantidade de Parcelas',
            'valor_total_nota': 'Valor Total da Nota',
            'informacoes_adicionais': 'Informacoes Adicionais',
        }
        widgets = {
            'emitente': forms.Select(attrs={'class': 'form-select'}),
            'destinatario': forms.Select(attrs={'class': 'form-select'}),
            'tipo_operacao': forms.Select(attrs={'class': 'form-select'}),
            'finalidade_emissao': forms.Select(attrs={'class': 'form-select'}),
            'data_emissao': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'data_saida': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'quantidade_parcelas': forms.NumberInput(attrs={'min': 1, 'step': 1, 'readonly': 'readonly', 'class': 'bg-light'}),
            'valor_total_desconto': forms.NumberInput(attrs={'step': '0.01'}),
            'informacoes_adicionais': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['emitente'].queryset = Empresa.objects.all().order_by('razao_social', 'nome')
        self.fields['destinatario'].queryset = Empresa.objects.all().order_by('razao_social', 'nome')

        self._naturezas_map = {}
        try:
            NaturezaOperacao = apps.get_model('fiscal', 'NaturezaOperacao')
            naturezas = NaturezaOperacao.objects.all().only('id', 'codigo', 'descricao')
            self.fields['natureza_operacao'].choices = [
                ('', 'Selecione a natureza de operacao'),
                *[(str(n.id), f"{(n.codigo or '').strip()} - {(n.descricao or '').strip()}".strip(' -')) for n in naturezas]
            ]
            self._naturezas_map = {str(n.id): n for n in naturezas}

            atual = (self.instance.natureza_operacao or '').strip() if self.instance else ''
            if atual:
                def _norm_nat(value):
                    return ' '.join(str(value or '').strip().lower().split())

                alvo_nat = _norm_nat(atual)
                match = ''
                for n in naturezas:
                    codigo = str(n.codigo or '').strip()
                    descricao = str(n.descricao or '').strip()
                    candidatos = {
                        _norm_nat(descricao),
                        _norm_nat(codigo),
                        _norm_nat(f"{codigo} - {descricao}"),
                    }
                    if alvo_nat in candidatos:
                        match = str(n.id)
                        break

                if match:
                    self.fields['natureza_operacao'].initial = match
                    self.initial['natureza_operacao'] = match
                else:
                    _ensure_current_value_choice(self.fields['natureza_operacao'], atual, label_prefix='Atual (importado)')
        except LookupError:
            self.fields['natureza_operacao'].choices = [('', 'Modulo Fiscal indisponivel')]

        self._condicoes_pagamento_map = {}
        self.fields['condicao_pagamento'].widget = CondicaoPagamentoSelect(attrs={'class': 'form-select'})
        try:
            CondicaoPagamento = apps.get_model('comercial', 'CondicaoPagamento')
            condicoes = CondicaoPagamento.objects.all().only('id', 'codigo', 'descricao', 'quantidade_parcelas', 'observacoes')
            self.fields['condicao_pagamento'].choices = [
                ('', 'Selecione a condicao de pagamento'),
                *[(str(c.id), f"{c.codigo} - {c.descricao}") for c in condicoes]
            ]
            self._condicoes_pagamento_map = {str(c.id): c for c in condicoes}
            self.fields['condicao_pagamento'].widget.condicoes_map = self._condicoes_pagamento_map

            atual = (self.instance.condicao_pagamento or '').strip() if self.instance else ''
            if atual:
                def _norm(value):
                    return ' '.join(str(value or '').strip().lower().split())

                alvo = _norm(atual)
                match = ''
                for c in condicoes:
                    codigo = str(c.codigo or '').strip()
                    descricao = str(c.descricao or '').strip()
                    candidatos = {
                        _norm(descricao),
                        _norm(codigo),
                        _norm(f"{codigo} - {descricao}"),
                    }
                    if alvo in candidatos:
                        match = str(c.id)
                        break

                if match:
                    self.fields['condicao_pagamento'].initial = match
                    self.initial['condicao_pagamento'] = match
                else:
                    _ensure_current_value_choice(self.fields['condicao_pagamento'], atual, label_prefix='Atual (importado)')
        except LookupError:
            self.fields['condicao_pagamento'].choices = [('', 'Modulo Comercial indisponivel')]

        if self.instance and self.instance.pk and not self.instance.tipo_operacao:
            self.fields['tipo_operacao'].initial = '0'
            self.initial['tipo_operacao'] = '0'

        self.fields['quantidade_parcelas'].widget.attrs['readonly'] = True
        self.fields['quantidade_parcelas'].widget.attrs['class'] = f"{self.fields['quantidade_parcelas'].widget.attrs.get('class', '')} bg-light".strip()

    def clean(self):
        cleaned_data = super().clean()

        natureza_id = (cleaned_data.get('natureza_operacao') or '').strip()
        if natureza_id and natureza_id in self._naturezas_map:
            cleaned_data['natureza_operacao'] = (self._naturezas_map[natureza_id].descricao or '').strip()
        elif self.instance and self.instance.pk:
            cleaned_data['natureza_operacao'] = self.instance.natureza_operacao

        condicao_id = (cleaned_data.get('condicao_pagamento') or '').strip()
        if condicao_id and condicao_id in self._condicoes_pagamento_map:
            condicao = self._condicoes_pagamento_map[condicao_id]
            cleaned_data['condicao_pagamento'] = (condicao.descricao or '').strip()
            cleaned_data['quantidade_parcelas'] = condicao.quantidade_parcelas or 1
        elif self.instance and self.instance.pk and self.instance.condicao_pagamento:
            cleaned_data['condicao_pagamento'] = self.instance.condicao_pagamento
            cleaned_data['quantidade_parcelas'] = self.instance.quantidade_parcelas or 1
        elif not cleaned_data.get('quantidade_parcelas'):
            cleaned_data['quantidade_parcelas'] = 1

        cleaned_data['tipo_operacao'] = '0'

        return cleaned_data


class ItemNotaFiscalForm(forms.ModelForm):
    class Meta:
        model = ItemNotaFiscal
        fields = ['codigo', 'descricao', 'ncm', 'cfop', 'unidade', 'quantidade', 'valor_unitario', 'valor_total', 'desconto', 'aliquota_icms', 'aliquota_ipi', 'aliquota_pis', 'aliquota_cofins', 'regra_icms_aplicada', 'regra_icms_descricao', 'aliquota_icms_origem', 'motor_versao', 'dados_contexto_regra']
        widgets = {
            'aliquota_icms': forms.HiddenInput(),
            'aliquota_ipi': forms.HiddenInput(),
            'aliquota_pis': forms.HiddenInput(),
            'aliquota_cofins': forms.HiddenInput(),
            'regra_icms_aplicada': forms.HiddenInput(),
            'regra_icms_descricao': forms.HiddenInput(),
            'aliquota_icms_origem': forms.HiddenInput(),
            'motor_versao': forms.HiddenInput(),
            'dados_contexto_regra': forms.HiddenInput(),
        }

    def clean_ncm(self):
        return normalizar_codigo_ncm(self.cleaned_data.get('ncm')) or None


class DuplicataNotaFiscalForm(forms.ModelForm):
    class Meta:
        model = DuplicataNotaFiscal
        fields = ['numero', 'vencimento', 'valor']
        widgets = {
            'vencimento': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'valor': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
        }


class TransporteNotaFiscalForm(forms.ModelForm):
    class Meta:
        model = TransporteNotaFiscal
        fields = ['modalidade_frete', 'transportadora', 'transportadora_nome', 'transportadora_cnpj', 'placa_veiculo', 'uf_veiculo', 'rntc', 'quantidade_volumes', 'especie_volumes', 'peso_liquido', 'peso_bruto']
        widgets = {
            'transportadora': forms.Select(attrs={'class': 'form-select'}),
            'quantidade_volumes': forms.NumberInput(attrs={'min': 0, 'step': 1}),
            'peso_liquido': forms.NumberInput(attrs={'step': '0.0001', 'min': '0'}),
            'peso_bruto': forms.NumberInput(attrs={'step': '0.0001', 'min': '0'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        categoria_transportadora = CategoriaEmpresa.objects.filter(nome__iexact='Transportadora').first()
        qs = Empresa.objects.filter(status_empresa='ativa')
        if categoria_transportadora:
            qs = qs.filter(categoria=categoria_transportadora)
        else:
            qs = qs.none()
        self.fields['transportadora'].queryset = qs.order_by('razao_social', 'nome')
        self.fields['transportadora'].required = False

        self.fields['modalidade_frete'].label = 'Modalidade do Frete'
        self.fields['placa_veiculo'].label = 'Placa do Veiculo'
        self.fields['uf_veiculo'].label = 'UF do Veiculo'
        self.fields['especie_volumes'].label = 'Especie dos Volumes'
        self.fields['peso_liquido'].label = 'Peso Liquido (kg)'
        self.fields['peso_bruto'].label = 'Peso Bruto (kg)'

        self.fields['modalidade_frete'].choices = [
            ('0', 'Contratacao do Frete por conta do Remetente (CIF)'),
            ('1', 'Contratacao do Frete por conta do Destinatario (FOB)'),
            ('2', 'Contratacao do Frete por conta de Terceiros'),
            ('3', 'Transporte Proprio por conta do Remetente'),
            ('4', 'Transporte Proprio por conta do Destinatario'),
            ('9', 'Sem Ocorrencia de Transporte'),
        ]

        transportadora = getattr(self.instance, 'transportadora', None)
        if transportadora:
            self.fields['transportadora_nome'].initial = self.instance.transportadora_nome or transportadora.razao_social or transportadora.nome
            self.fields['transportadora_cnpj'].initial = self.instance.transportadora_cnpj or transportadora.cnpj or transportadora.cpf

    @staticmethod
    def _normalizar_cnpj(value):
        return ''.join(ch for ch in str(value or '') if ch.isdigit())

    def save(self, commit=True):
        instance = super().save(commit=False)
        selected = self.cleaned_data.get('transportadora')
        nome = (self.cleaned_data.get('transportadora_nome') or '').strip()
        cnpj_raw = (self.cleaned_data.get('transportadora_cnpj') or '').strip()
        cnpj = self._normalizar_cnpj(cnpj_raw)

        if selected:
            instance.transportadora = selected
            if not nome:
                instance.transportadora_nome = selected.razao_social or selected.nome
            if not cnpj_raw and selected.cnpj:
                instance.transportadora_cnpj = selected.cnpj
        elif nome or cnpj:
            transportadora = None
            if cnpj:
                transportadora = Empresa.objects.filter(cnpj=cnpj).first()
            if not transportadora and nome:
                transportadora = Empresa.objects.filter(razao_social__iexact=nome).first() or Empresa.objects.filter(nome__iexact=nome).first()
            if not transportadora:
                categoria_transportadora = CategoriaEmpresa.objects.filter(nome__iexact='Transportadora').first()
                if not categoria_transportadora:
                    categoria_transportadora = CategoriaEmpresa.objects.create(nome='Transportadora')
                transportadora = Empresa.objects.create(
                    tipo_empresa='pj',
                    razao_social=nome or f'Transportadora {cnpj}',
                    nome_fantasia=nome or None,
                    cnpj=cnpj or None,
                    categoria=categoria_transportadora,
                    fornecedor=True,
                    status_empresa='ativa',
                )
            instance.transportadora = transportadora
            if not instance.transportadora_nome:
                instance.transportadora_nome = transportadora.razao_social or transportadora.nome
            if not instance.transportadora_cnpj and transportadora.cnpj:
                instance.transportadora_cnpj = transportadora.cnpj

        if commit:
            instance.save()
        return instance


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
    extra=0,
    can_delete=False,
    fk_name='nota_fiscal'
)

TransporteNotaFiscalFormSet = inlineformset_factory(
    NotaFiscal,
    TransporteNotaFiscal,
    form=TransporteNotaFiscalForm,
    extra=1,
    max_num=1,
    validate_max=True,
    can_delete=False,
    fk_name='nota_fiscal'
)


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
        option['attrs']['data-dias'] = (condicao.observacoes or '').strip()
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
            condicoes = CondicaoPagamento.objects.all().only('id', 'codigo', 'descricao', 'quantidade_parcelas', 'observacoes')
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
        cleaned_data['tipo_operacao'] = '1'
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









