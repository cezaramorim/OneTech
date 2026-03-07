from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django.contrib.auth.models import Group

from .models import GroupProfile

User = get_user_model()


class SignUpForm(UserCreationForm):
    nome_completo = forms.CharField(
        max_length=255,
        label="Nome Completo",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Nome completo",
            }
        ),
    )

    whatsapp = forms.CharField(
        max_length=20,
        label="WhatsApp",
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "(Opcional) Numero com DDD",
            }
        ),
    )

    grupo = forms.ModelChoiceField(
        queryset=Group.objects.all(),
        label="Grupo",
        required=True,
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    is_active = forms.BooleanField(
        label="Ativo",
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + (
            "nome_completo",
            "whatsapp",
            "grupo",
            "is_active",
        )
        widgets = {
            "username": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Usuario",
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "E-mail",
                    "autocomplete": "off",
                }
            ),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.nome_completo = self.cleaned_data["nome_completo"]
        user.whatsapp = self.cleaned_data.get("whatsapp")
        user.is_active = self.cleaned_data["is_active"]

        if commit:
            user.save()
            user.groups.set([self.cleaned_data["grupo"]])

        return user


class EditUserForm(UserChangeForm):
    password = None

    username = forms.CharField(
        label="Nome de Usuario (Login)",
        required=False,
        disabled=True,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "readonly": "readonly",
            }
        ),
    )

    new_password1 = forms.CharField(
        label="Nova Senha",
        required=False,
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Digite a nova senha",
                "autocomplete": "off",
            }
        ),
    )

    new_password2 = forms.CharField(
        label="Confirme a Nova Senha",
        required=False,
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Confirme a nova senha",
                "autocomplete": "off",
            }
        ),
    )

    current_password = forms.CharField(
        label="Senha Atual",
        required=False,
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Confirme sua senha para salvar",
                "autocomplete": "current-password",
            }
        ),
    )

    grupo = forms.ModelChoiceField(
        queryset=Group.objects.all(),
        label="Grupo",
        required=True,
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    class Meta:
        model = User
        fields = ("username", "email", "nome_completo", "whatsapp", "grupo", "is_active")
        widgets = {
            "email": forms.EmailInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "E-mail",
                    "autocomplete": "off",
                }
            ),
            "nome_completo": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Nome Completo",
                    "autocomplete": "off",
                }
            ),
            "whatsapp": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Numero com DDD",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        request_user = kwargs.pop("request_user", None)
        super().__init__(*args, **kwargs)

        self.fields["username"].initial = self.instance.username
        self.fields["grupo"].initial = self.instance.groups.first()

        if request_user and not request_user.is_superuser:
            self.fields.pop("grupo")

    def clean(self):
        cleaned_data = super().clean()
        current_password = cleaned_data.get("current_password")
        new_password1 = cleaned_data.get("new_password1")
        new_password2 = cleaned_data.get("new_password2")

        if new_password1:
            if not current_password:
                raise forms.ValidationError(
                    {"current_password": "Este campo e obrigatorio para alterar a senha."}
                )
            if not self.instance.check_password(current_password):
                raise forms.ValidationError({"current_password": "A senha atual esta incorreta."})
            if not new_password2:
                raise forms.ValidationError({"new_password2": "Por favor, confirme a nova senha."})
            if new_password1 != new_password2:
                raise forms.ValidationError({"new_password2": "As senhas informadas nao coincidem."})
            if len(new_password1) < 6:
                raise forms.ValidationError(
                    {"new_password1": "A nova senha deve conter pelo menos 6 caracteres."}
                )
            if self.instance.check_password(new_password1):
                raise forms.ValidationError(
                    {"new_password1": "A nova senha nao pode ser igual a senha atual."}
                )
        elif new_password2:
            raise forms.ValidationError({"new_password1": "Por favor, digite a nova senha."})

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        new_password = self.cleaned_data.get("new_password1")

        if new_password:
            user.set_password(new_password)

        if commit:
            user.save()
            if "grupo" in self.cleaned_data:
                user.groups.set([self.cleaned_data["grupo"]])

        return user


class GroupForm(forms.ModelForm):
    name = forms.CharField(
        label="Nome do Grupo",
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    finalidade = forms.CharField(
        label="Finalidade",
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    is_active = forms.BooleanField(
        label="Ativo",
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )

    class Meta:
        model = GroupProfile
        fields = ["name", "finalidade", "is_active"]
