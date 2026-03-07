from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.test import TestCase
from django.urls import reverse

from accounts.forms import EditUserForm, SignUpForm


class PermissionSeparationTests(TestCase):
    def setUp(self):
        self.user_model = get_user_model()
        self.group_a = Group.objects.create(name="Operacao A")
        self.group_b = Group.objects.create(name="Operacao B")
        self.perm_add_user = Permission.objects.get(
            content_type__app_label="accounts",
            codename="add_user",
        )
        self.perm_change_user = Permission.objects.get(
            content_type__app_label="accounts",
            codename="change_user",
        )
        self.perm_view_user = Permission.objects.get(
            content_type__app_label="accounts",
            codename="view_user",
        )
        self.group_a.permissions.set([self.perm_add_user, self.perm_change_user])
        self.group_b.permissions.set([self.perm_add_user])
        self.admin = self.user_model.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="admin123",
        )

    def test_signup_form_keeps_group_permissions_out_of_user_permissions(self):
        form = SignUpForm(
            data={
                "username": "novo",
                "nome_completo": "Usuario Novo",
                "email": "novo@example.com",
                "whatsapp": "11999999999",
                "grupo": self.group_a.id,
                "is_active": True,
                "password1": "segredo123",
                "password2": "segredo123",
            }
        )

        self.assertTrue(form.is_valid(), form.errors)
        user = form.save()

        self.assertEqual(user.groups.first(), self.group_a)
        self.assertEqual(set(user.user_permissions.all()), set())
        self.assertTrue(user.has_perm("accounts.add_user"))

    def test_edit_user_form_preserves_direct_permissions_instead_of_overwriting_with_group(self):
        user = self.user_model.objects.create_user(
            username="colaborador",
            email="colaborador@example.com",
            password="segredo123",
        )
        user.groups.set([self.group_a])
        user.user_permissions.add(self.perm_view_user)

        form = EditUserForm(
            data={
                "username": user.username,
                "email": "colaborador@example.com",
                "nome_completo": "Colaborador",
                "whatsapp": "11999999999",
                "grupo": self.group_b.id,
                "is_active": True,
                "new_password1": "",
                "new_password2": "",
                "current_password": "",
            },
            instance=user,
            request_user=self.admin,
        )

        self.assertTrue(form.is_valid(), form.errors)
        updated_user = form.save()

        self.assertEqual(updated_user.groups.first(), self.group_b)
        self.assertEqual(set(updated_user.user_permissions.all()), {self.perm_view_user})

    def test_user_permission_screen_distinguishes_direct_and_group_permissions(self):
        user = self.user_model.objects.create_user(
            username="analista",
            email="analista@example.com",
            password="segredo123",
        )
        user.groups.set([self.group_a])
        user.user_permissions.add(self.perm_change_user)

        self.client.force_login(self.admin)
        response = self.client.get(
            reverse("accounts:gerenciar_permissoes_usuario", args=[user.id])
        )

        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertIn("Esta tela edita apenas permissoes diretas do usuario.", html)
        self.assertIn("Via grupo", html)
        self.assertIn("Direta + grupo", html)

        post_response = self.client.post(
            reverse("accounts:gerenciar_permissoes_usuario", args=[user.id]),
            {"permissoes": []},
        )

        self.assertEqual(post_response.status_code, 302)
        user.refresh_from_db()
        self.assertEqual(set(user.user_permissions.all()), set())
        self.assertTrue(user.has_perm("accounts.add_user"))
