# control/forms.py
from django import forms
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from .models import Tenant
from accounts.models import User
from django.contrib.auth.models import Group

class TenantForm(forms.ModelForm):
    """Formulário para Criar e Editar Tenants."""
    admin_user = forms.CharField(
        label="Username do Administrador", required=False,
        help_text="Obrigatório ao criar. Este será o login do superusuário do tenant."
    )
    admin_email = forms.EmailField(
        label="E-mail do Administrador", required=False,
        help_text="Obrigatório ao criar. Um superusuário será criado para o tenant com este e-mail."
    )
    admin_pass = forms.CharField(
        label="Senha do Administrador", widget=forms.PasswordInput, required=False,
        help_text="Obrigatório ao criar. Defina uma senha forte."
    )

    class Meta:
        model = Tenant
        exclude = ['db_name', 'db_user', 'db_password', 'db_host', 'db_port']
        # Widgets e help_texts para uma UI mais clara...
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'slug': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: cliente-a'}),
            'dominio': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: cliente-a.meusite.com'}),
            'razao_social': forms.TextInput(attrs={'class': 'form-control'}),
            'nome_fantasia': forms.TextInput(attrs={'class': 'form-control'}),
            'cnpj': forms.TextInput(attrs={'class': 'form-control'}),
            'ie': forms.TextInput(attrs={'class': 'form-control'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'logo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'certificado_a1': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'senha_certificado': forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Deixe em branco para não alterar'}),
            'csc': forms.TextInput(attrs={'class': 'form-control'}),
            'id_token': forms.TextInput(attrs={'class': 'form-control'}),
        }
        help_texts = {
            'slug': 'Identificador único para URLs. Apenas letras minúsculas, números e hífens.',
            'dominio': 'O endereço web que este cliente usará para acessar o sistema.',
        }

    def __init__(self, *args, **kwargs):
        is_creation = kwargs.pop('is_creation', False)
        super().__init__(*args, **kwargs)
        if is_creation:
            self.fields['admin_user'].required = True
            self.fields['admin_email'].required = True
            self.fields['admin_pass'].required = True
        else:
            self.fields.pop('admin_user')
            self.fields.pop('admin_email')
            self.fields.pop('admin_pass')
        if self.instance and self.instance.pk:
            self.fields['senha_certificado'].required = False

class TenantUserCreationForm(forms.ModelForm):
    """Formulário para um admin global criar um usuário para um tenant."""
    password = forms.CharField(label='Senha', widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    grupo = forms.ModelChoiceField(queryset=Group.objects.none(), label="Grupo", required=True, widget=forms.Select(attrs={'class': 'form-select'}))

    class Meta:
        model = User
        fields = ('username', 'nome_completo', 'email', 'grupo', 'is_active')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'nome_completo': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
            grupo = self.cleaned_data['grupo']
            user.groups.set([grupo])
        return user

class TenantUserChangeForm(forms.ModelForm):
    """Formulário para um admin global editar um usuário de um tenant."""
    password = ReadOnlyPasswordHashField(
        label="Senha",
        help_text='Para alterar a senha, use o <a href="../password/">formulário de alteração de senha</a>.'
    )
    grupo = forms.ModelChoiceField(queryset=Group.objects.none(), label="Grupo", required=True, widget=forms.Select(attrs={'class': 'form-select'}))

    class Meta:
        model = User
        fields = ('username', 'nome_completo', 'email', 'grupo', 'is_active')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'nome_completo': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def save(self, commit=True):
        user = super().save(commit=True)
        if 'grupo' in self.cleaned_data:
            grupo = self.cleaned_data['grupo']
            user.groups.set([grupo])
        return user


# ==============================================================================
# 🚀 FORMULÁRIO PARA EMITENTE (MATRIZ/FILIAIS)
# ==============================================================================
from .models import Emitente

class EmitenteForm(forms.ModelForm):
    class Meta:
        model = Emitente
        fields = '__all__'
        widgets = {
            'razao_social': forms.TextInput(attrs={'class': 'form-control'}),
            'nome_fantasia': forms.TextInput(attrs={'class': 'form-control'}),
            'cnpj': forms.TextInput(attrs={'class': 'form-control'}),
            'ie': forms.TextInput(attrs={'class': 'form-control'}),
            'cep': forms.TextInput(attrs={'class': 'form-control'}),
            'logradouro': forms.TextInput(attrs={'class': 'form-control'}),
            'numero': forms.TextInput(attrs={'class': 'form-control'}),
            'complemento': forms.TextInput(attrs={'class': 'form-control'}),
            'bairro': forms.TextInput(attrs={'class': 'form-control'}),
            'cidade': forms.TextInput(attrs={'class': 'form-control'}),
            'uf': forms.TextInput(attrs={'class': 'form-control'}),
            'telefone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'logotipo': forms.FileInput(attrs={'class': 'form-control'}),
            'is_default': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }