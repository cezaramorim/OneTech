from django import forms

from .models import CategoriaEmpresa, EmpresaAvancada


class CategoriaEmpresaForm(forms.ModelForm):
    class Meta:
        model = CategoriaEmpresa
        fields = ['nome']
        widgets = {
            'nome': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Digite o nome da categoria',
                }
            )
        }



# Formulario oficial do fluxo atual, associado a `empresas_empresaavancada`.
class EmpresaForm(forms.ModelForm):
    class Meta:
        model = EmpresaAvancada
        fields = '__all__'
        widgets = {
            'tipo_empresa': forms.Select(attrs={'class': 'form-select'}),
            'razao_social': forms.TextInput(attrs={'class': 'form-control'}),
            'nome_fantasia': forms.TextInput(attrs={'class': 'form-control'}),
            'cnpj': forms.TextInput(attrs={'class': 'form-control'}),
            'ie': forms.TextInput(attrs={'class': 'form-control'}),
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'cpf': forms.TextInput(attrs={'class': 'form-control'}),
            'rg': forms.TextInput(attrs={'class': 'form-control'}),
            'profissao': forms.TextInput(attrs={'class': 'form-control'}),
            'cnae_principal': forms.TextInput(attrs={'class': 'form-control'}),
            'cnae_secundario': forms.TextInput(attrs={'class': 'form-control'}),
            'data_abertura': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date'}),
            'data_cadastro': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date'}),
            'cep': forms.TextInput(attrs={'class': 'form-control mascara-cep', 'id': 'cep'}),
            'logradouro': forms.TextInput(attrs={'class': 'form-control', 'id': 'logradouro'}),
            'numero': forms.TextInput(attrs={'class': 'form-control'}),
            'complemento': forms.TextInput(attrs={'class': 'form-control'}),
            'bairro': forms.TextInput(attrs={'class': 'form-control', 'id': 'bairro'}),
            'cidade': forms.TextInput(attrs={'class': 'form-control', 'id': 'cidade'}),
            'uf': forms.TextInput(attrs={'class': 'form-control', 'id': 'uf'}),
            'telefone': forms.TextInput(attrs={'class': 'form-control mascara-telefone'}),
            'celular': forms.TextInput(attrs={'class': 'form-control mascara-celular'}),
            'whatsapp': forms.TextInput(attrs={'class': 'form-control mascara-celular'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'site': forms.URLInput(attrs={'class': 'form-control'}),
            'contato_financeiro_nome': forms.TextInput(attrs={'class': 'form-control'}),
            'contato_financeiro_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'contato_financeiro_telefone': forms.TextInput(attrs={'class': 'form-control mascara-telefone'}),
            'contato_financeiro_celular': forms.TextInput(attrs={'class': 'form-control mascara-celular'}),
            'contato_comercial_nome': forms.TextInput(attrs={'class': 'form-control'}),
            'contato_comercial_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'contato_comercial_telefone': forms.TextInput(attrs={'class': 'form-control mascara-telefone'}),
            'contato_comercial_celular': forms.TextInput(attrs={'class': 'form-control mascara-celular'}),
            'condicao_pagamento': forms.TextInput(attrs={'class': 'form-control'}),
            'comissao': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'vendedor': forms.Select(attrs={'class': 'form-select'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            'status_empresa': forms.Select(attrs={'class': 'form-select'}),
            'cliente': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'fornecedor': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'regime_tributario': forms.Select(attrs={'class': 'form-select'}),
            'contribuinte_icms': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'inscricao_municipal': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        tipo = None

        if 'tipo_empresa' in self.data:
            tipo = self.data.get('tipo_empresa')
        elif self.instance and self.instance.pk:
            if self.instance.cnpj:
                tipo = 'pj'
            elif self.instance.cpf:
                tipo = 'pf'
        elif self.initial.get('tipo_empresa'):
            tipo = self.initial.get('tipo_empresa')

        if tipo == 'pj':
            obrigatorios = [
                'tipo_empresa',
                'razao_social',
                'cnpj',
                'cep',
                'logradouro',
                'numero',
                'bairro',
                'cidade',
                'uf',
            ]
        elif tipo == 'pf':
            obrigatorios = [
                'tipo_empresa',
                'nome',
                'cpf',
                'cep',
                'logradouro',
                'numero',
                'bairro',
                'cidade',
                'uf',
            ]
        else:
            obrigatorios = ['tipo_empresa']

        for field in obrigatorios:
            if field in self.fields:
                self.fields[field].required = True

