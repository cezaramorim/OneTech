from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth.models import Group
from .models import User
from django.contrib.auth import get_user_model

User = get_user_model()

# === Formulário de Cadastro ===
class SignUpForm(UserCreationForm):
    nome_completo = forms.CharField(
        max_length=255,
        label="Nome Completo",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nome completo'
        })
    )

    grupo = forms.ModelChoiceField(
        queryset=Group.objects.all(),
        label="Grupo",
        required=True,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'nome_completo', 'grupo', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Usuário'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'E-mail',
                'autocomplete': 'off'
            }),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.nome_completo = self.cleaned_data['nome_completo']

        if commit:
            user.save()
            grupo = self.cleaned_data['grupo']
            user.groups.set([grupo])

            # 🔁 HERANÇA AUTOMÁTICA: copiar permissões do grupo ao usuário
            permissoes_grupo = grupo.permissions.all()
            user.user_permissions.set(permissoes_grupo)

        return user


# === Formulário de Edição ===
class EditUserForm(UserChangeForm):
    password = None  # Oculta o campo de senha atual herdado

    username = forms.CharField(
        label="Nome de Usuário (Login)",
        required=False,
        disabled=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'readonly': 'readonly'
        })
    )

    new_password1 = forms.CharField(
        label="Nova Senha",
        required=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Digite a nova senha',
            'autocomplete': 'off'
        })
    )

    new_password2 = forms.CharField(
        label="Confirme a Nova Senha",
        required=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirme a nova senha',
            'autocomplete': 'off'
        })
    )

    grupo = forms.ModelChoiceField(
        queryset=Group.objects.all(),
        label="Grupo",
        required=True,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'nome_completo', 'grupo')
        widgets = {
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'E-mail',
                'autocomplete': 'off'
            }),
            'nome_completo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome Completo',
                'autocomplete': 'off'
            }),
        }

    def __init__(self, *args, **kwargs):
        request_user = kwargs.pop('request_user', None)
        super().__init__(*args, **kwargs)

        # Define o valor do username manualmente
        self.fields['username'].initial = self.instance.username

        # Somente superusuários podem editar o grupo
        if request_user and not request_user.is_superuser:
            self.fields.pop('grupo')

    def clean(self):
        cleaned_data = super().clean()
        pw1 = cleaned_data.get("new_password1")
        pw2 = cleaned_data.get("new_password2")

        if pw1 or pw2:
            if pw1 != pw2:
                raise forms.ValidationError("As senhas informadas não coincidem.")
            if len(pw1) < 6:
                raise forms.ValidationError("A nova senha deve conter pelo menos 6 caracteres.")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        new_password = self.cleaned_data.get("new_password1")

        if new_password:
            user.set_password(new_password)

        if commit:
            user.save()

            # Se campo grupo existir, associar grupo + herança de permissões
            if 'grupo' in self.cleaned_data:
                grupo = self.cleaned_data['grupo']
                user.groups.set([grupo])

                # 🔁 HERANÇA AUTOMÁTICA: copiar permissões do grupo ao usuário
                permissoes_grupo = grupo.permissions.all()
                user.user_permissions.set(permissoes_grupo)

        return user



