from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth.models import Group
from .models import User, GroupProfile
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

    whatsapp = forms.CharField(
        max_length=20,
        label="WhatsApp",
        required=False,  # Opcional no cadastro
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '(Opcional) Número com DDD'
        })
    )

    grupo = forms.ModelChoiceField(
        queryset=Group.objects.all(),
        label="Grupo",
        required=True,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    is_active = forms.BooleanField(
        label="Ativo",
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('nome_completo', 'whatsapp', 'grupo', 'is_active')
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
        user.whatsapp = self.cleaned_data.get('whatsapp')  # .get() para segurança
        user.is_active = self.cleaned_data['is_active']

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

    current_password = forms.CharField(
        label="Senha Atual",
        required=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirme sua senha para salvar',
            'autocomplete': 'current-password'
        })
    )
    
    # ←── Aqui adicionamos o campo "grupo" na edição
    grupo = forms.ModelChoiceField(
        queryset=Group.objects.all(),
        label="Grupo",
        required=True,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'nome_completo', 'whatsapp', 'grupo', 'is_active')
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
            'whatsapp': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Número com DDD'
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
        current_password = cleaned_data.get("current_password")
        new_password1 = cleaned_data.get("new_password1")
        new_password2 = cleaned_data.get("new_password2")

        # Only proceed with password validation if new_password1 is provided
        if new_password1:
            # Current password is required if new password is provided
            if not current_password:
                raise forms.ValidationError({'current_password': "Este campo é obrigatório para alterar a senha."})
            elif not self.instance.check_password(current_password):
                raise forms.ValidationError({'current_password': "A senha atual está incorreta."})

            # New password validation
            if not new_password2:
                raise forms.ValidationError({'new_password2': "Por favor, confirme a nova senha."})
            if new_password1 != new_password2:
                raise forms.ValidationError({'new_password2': "As senhas informadas não coincidem."})
            if len(new_password1) < 6:
                raise forms.ValidationError({'new_password1': "A nova senha deve conter pelo menos 6 caracteres."})
            if self.instance.check_password(new_password1):
                raise forms.ValidationError({'new_password1': "A nova senha não pode ser igual à senha atual."})
        elif new_password2: # If new_password2 is provided but new_password1 is not.
            raise forms.ValidationError({'new_password1': "Por favor, digite a nova senha."})

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

class GroupForm(forms.ModelForm):
    name = forms.CharField(
        label="Nome do Grupo",
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    finalidade = forms.CharField(
        label="Finalidade",
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    is_active = forms.BooleanField(
        label="Ativo",
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    class Meta:
        model = GroupProfile
        fields = ['name', 'finalidade', 'is_active']