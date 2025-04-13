from django import forms
from .models import Empresa, CategoriaEmpresa

# === Formulário de Categoria ===
class CategoriaEmpresaForm(forms.ModelForm):
    class Meta:
        model = CategoriaEmpresa
        fields = ['nome']
        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Digite o nome da categoria'
            })
        }


# === Formulário de Empresa ===
class EmpresaForm(forms.ModelForm):
    categoria = forms.ModelChoiceField(
        queryset=CategoriaEmpresa.objects.all(),
        empty_label="Selecione uma categoria",
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = Empresa
        fields = [
            'nome_empresa',
            'nome_fantasia',
            'tipo_empresa',
            'cnae',
            'cnae_secundario',
            'cnpj',
            'inscricao_estadual',
            'rua',
            'numero',
            'complemento',
            'bairro',
            'cidade',
            'estado',
            'cep',
            'telefone_principal',
            'telefone_secundario',
            'email_contato',
            'site',
            'nome_representante',
            'celular_representante',
            'email_representante',
            'status_empresa',
            'categoria'
        ]
        widgets = {
            'nome_empresa': forms.TextInput(attrs={'class': 'form-control'}),
            'nome_fantasia': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo_empresa': forms.Select(attrs={'class': 'form-select'}),
            'cnae': forms.TextInput(attrs={'class': 'form-control'}),
            'cnae_secundario': forms.TextInput(attrs={'class': 'form-control'}),
            'cnpj': forms.TextInput(attrs={'class': 'form-control'}),
            'inscricao_estadual': forms.TextInput(attrs={'class': 'form-control'}),

            'rua': forms.TextInput(attrs={'class': 'form-control'}),
            'numero': forms.TextInput(attrs={'class': 'form-control'}),
            'complemento': forms.TextInput(attrs={'class': 'form-control'}),
            'bairro': forms.TextInput(attrs={'class': 'form-control'}),
            'cidade': forms.TextInput(attrs={'class': 'form-control'}),
            'estado': forms.TextInput(attrs={'class': 'form-control'}),
            'cep': forms.TextInput(attrs={'class': 'form-control'}),

            'telefone_principal': forms.TextInput(attrs={'class': 'form-control'}),
            'telefone_secundario': forms.TextInput(attrs={'class': 'form-control'}),
            'email_contato': forms.EmailInput(attrs={'class': 'form-control'}),
            'site': forms.URLInput(attrs={'class': 'form-control'}),

            'nome_representante': forms.TextInput(attrs={'class': 'form-control'}),
            'celular_representante': forms.TextInput(attrs={'class': 'form-control'}),
            'email_representante': forms.EmailInput(attrs={'class': 'form-control'}),

            'status_empresa': forms.Select(attrs={'class': 'form-select'}),
        }
