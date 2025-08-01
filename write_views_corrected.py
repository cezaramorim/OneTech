
import os

corrected_views_content = """from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import Permission, Group, User
from django.http import JsonResponse
from django.contrib import messages
from django.urls import reverse
from django.views.decorators.http import require_POST
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordResetForm
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
import json

from .forms import SignUpForm, EditUserForm, GroupForm
from .models import User, GroupProfile
from accounts.utils import PERMISSOES_PT_BR, is_super_or_group_admin, render_ajax_or_base, enviar_link_whatsapp


# === Autenticação ===
def signup_view(request):
    form = SignUpForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            user = form.save()
            login(request, user)
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'redirect_url': '/'})
            return redirect('painel:home')
        elif request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)

    template = 'partials/accounts/signup.html' if request.headers.get('x-requested-with') == 'XMLHttpRequest' else 'base.html'
    context = {'form': form} if 'partials' in template else {'form': form, 'content_template': 'partials/accounts/signup.html'}
    return render(request, template, context)

def login_view(request):
    error = None

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        print(f"Attempting to authenticate user: {username} with password: {password}")
        user = authenticate(request, username=username, password=password)
        print(f"Authentication result for {username}: {user} (type: {type(user)})")

        if user:
            login(request, user)

            # ✅ Se for AJAX, retorna JSON com a URL do painel
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'redirect_url': reverse('painel:home')})

            # ✅ Redirecionamento padrão (acesso não-AJAX)
            return redirect('painel:home')

        # ❌ Credenciais inválidas
        error = "Usuário ou senha inválidos."

        # ⚠️ Se for AJAX, retorna JSON com mensagem de erro
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': error})

    # 📄 Exibição do formulário
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'
    template = 'partials/accounts/login.html' if is_ajax else 'accounts/login_full.html'
    return render(request, template, {'error': error})



@login_required
def logout_view(request):
    if request.method == 'POST':
        logout(request)
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'redirect_url': '/accounts/login/'})
        return redirect('accounts:login')

    template = 'partials/accounts/logout.html' if request.headers.get('x-requested-with') == 'XMLHttpRequest' else 'base.html'
    context = {} if 'partials' in template else {'content_template': 'partials/accounts/logout.html'}
    return render(request, template, context)

@login_required
def edit_profile_view(request):
    form = EditUserForm(request.POST or None, instance=request.user, request_user=request.user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Dados salvos com sucesso!')

    template = 'partials/accounts/edit_profile.html' if request.headers.get('x-requested-with') == 'XMLHttpRequest' else 'base.html'
    context = {'form': form} if 'partials' in template else {'form': form, 'content_template': 'partials/accounts/edit_profile.html'}
    return render(request, template, context)

@login_required
@user_passes_test(is_super_or_group_admin)
def criar_usuario(request):
    form = SignUpForm(request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            novo_usuario = form.save()

            msg = "Usuário criado com sucesso com permissões herdadas do grupo."

            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                # ✅ Retorna JSON com sucesso e mensagem
                return JsonResponse({
                    'success': True,
                    'message': msg,
                    'redirect_url': reverse('accounts:lista_usuarios')
                })

            # ✅ Comum: exibe mensagem e redireciona
            messages.success(request, msg)
            return redirect('accounts:lista_usuarios')

        else:
            erro_msg = 'Erro ao criar usuário. Verifique os campos.'

            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                # ❌ Retorna erros e mensagem via JSON
                return JsonResponse({
                    'success': False,
                    'errors': form.errors,
                    'message': erro_msg
                }, status=400)

            # ❌ Comum: exibe erro e renderiza novamente o formulário
            messages.error(request, erro_msg)

    # 🧾 GET inicial ou POST inválido sem AJAX
    return render_ajax_or_base(request, 'partials/accounts/criar_usuario.html', {
        'form': form,
        'data_page': 'criar_usuario'
    })


@login_required
def lista_usuarios(request):
    usuarios = User.objects.all()
    template = 'partials/accounts/lista_usuarios.html' if request.headers.get('x-requested-with') == 'XMLHttpRequest' else 'base.html'
    context = {
        'usuarios': usuarios,
        'data_page': 'lista_usuarios'
    } if 'partials' in template else {
        'usuarios': usuarios,
        'content_template': 'partials/accounts/lista_usuarios.html',
        'data_page': 'lista_usuarios'
    }
    return render(request, template, context)


@login_required
@user_passes_test(is_super_or_group_admin)
def editar_usuario(request, usuario_id):
    usuario = get_object_or_404(User, id=usuario_id)
    form = EditUserForm(request.POST or None, instance=usuario, request_user=request.user)
    grupos = Group.objects.all()
    grupo_atual = usuario.groups.first()

    if request.method == 'POST':
        nova_senha = request.POST.get('nova_senha')
        confirmar = request.POST.get('confirmar_senha')

        if nova_senha and nova_senha == confirmar:
            usuario.set_password(nova_senha)

        grupo_id = request.POST.get('grupo')
        if grupo_id:
            grupo = get_object_or_404(Group, id=grupo_id)
            usuario.groups.clear()
            usuario.groups.add(grupo)

        if form.is_valid():
            form.save()
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'sucesso': True,
                    'mensagem': 'Usuário atualizado com sucesso!',
                    'redirect_url': reverse('accounts:lista_usuarios')
                })
            return redirect('accounts:lista_usuarios')
        else:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                erros = []
                for field, msgs in form.errors.items():
                    for msg in msgs:
                        label = form.fields[field].label if field in form.fields else field
                        erros.append(f"{label}: {msg}")
                return JsonResponse({
                    'sucesso': False,
                    'mensagem': "Erro ao atualizar usuário:<br>" + "<br>".join(erros)
                }, status=400)

    # ✅ Aqui está o ponto importante
    contexto = {
        'form': form,
        'usuario': usuario,
        'grupo_atual': grupo_atual,
        'grupos': grupos,
        'data_page': 'editar_usuario',
    }

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'partials/accounts/editar_usuario.html', contexto)

    return render(request, 'base.html', {
        'content_template': 'partials/accounts/editar_usuario.html',
        **contexto
    })

import json

@login_required
@require_POST
@user_passes_test(is_super_or_group_admin)
def excluir_usuario_multiplo(request):
    try:
        data = json.loads(request.body)
        ids = data.get('ids', [])
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Dados inválidos.'}, status=400)

    if not ids:
        return JsonResponse({'success': False, 'message': 'Nenhum usuário selecionado para exclusão.'}, status=400)

    usuarios = User.objects.filter(id__in=ids)
    count = usuarios.count()
    usuarios.delete()

    msg = f'{count} usuário(s) excluído(s) com sucesso.'
    return JsonResponse({
        'success': True,
        'message': msg,
        'redirect_url': reverse('accounts:lista_usuarios')
    })

@login_required
@user_passes_test(is_super_or_group_admin)
def selecionar_usuario_permissoes_view(request):
    usuarios = User.objects.all().order_by('username')
    return render_ajax_or_base(
        request,
        'partials/accounts/selecionar_usuario_permissoes.html',
        {'usuarios': usuarios}
    )

@login_required
@user_passes_test(is_super_or_group_admin)
def editar_permissoes(request, usuario_id):
    """
    View para editar permissões de um usuário específico.
    Exibe permissões agrupadas por app_label com nomes traduzidos.
    """
    usuario = get_object_or_404(User, id=usuario_id)

    # Mapeamento fixo de nomes traduzidos de apps
    NOMES_APPS = {
        'auth': 'Permissões',
        'admin': 'Administração',
        'sessions': 'Sessões',
        'accounts': 'Usuários',
        'contenttypes': 'Tipos de Conteúdo',
        'empresas': 'Empresas',
        'nota_fiscal': 'Nota Fiscal',
        'produto': 'Produtos',
    }

    permissoes = Permission.objects.select_related('content_type').order_by(
        'content_type__app_label', 'codename'
    )

    permissoes_agrupadas = {}
    nomes_apps_traduzidos = {}

    for p in permissoes:
        app = p.content_type.app_label
        p.traduzida = PERMISSOES_PT_BR.get(p.name, p.name)
        permissoes_agrupadas.setdefault(app, []).append(p)
        if app not in nomes_apps_traduzidos:
            nomes_apps_traduzidos[app] = NOMES_APPS.get(app, app.capitalize())

    if request.method == 'POST':
        permissoes_ids = request.POST.getlist('permissoes')
        usuario.user_permissions.set(permissoes_ids)
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': 'Permissões atualizadas com sucesso!',
                'redirect_url': reverse('accounts:seletor_usuario_permissoes')
            })

    permissoes_usuario = usuario.user_permissions.all()

    return render_ajax_or_base(
        request,
        'partials/accounts/editar_permissoes.html',
        {
            'usuario': usuario,
            'permissoes_agrupadas': permissoes_agrupadas,
            'permissoes_usuario': permissoes_usuario,
            'nomes_apps_traduzidos': nomes_apps_traduzidos,
        }
    )

# === Grupos ===

@login_required
@user_passes_test(is_super_or_group_admin)
def lista_grupos(request):
    grupos = Group.objects.prefetch_related('profile').all()
    return render_ajax_or_base(
        request,
        'partials/accounts/lista_grupos.html',
        {'grupos': grupos}
    )

@login_required
@user_passes_test(is_super_or_group_admin)
def cadastrar_grupo(request):
    if request.method == 'POST':
        form = GroupForm(request.POST)
        if form.is_valid():
            group = Group.objects.create(name=form.cleaned_data['name'])
            profile = GroupProfile.objects.create(
                group=group,
                is_active=form.cleaned_data['is_active'],
                finalidade=form.cleaned_data['finalidade']
            )
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'redirect_url': reverse('accounts:lista_grupos')})
            return redirect('accounts:lista_grupos')
    else:
        form = GroupForm()
    return render_ajax_or_base(request, 'partials/accounts/cadastrar_grupo.html', {'form': form})

@login_required
@user_passes_test(is_super_or_group_admin)
def editar_grupo(request, grupo_id):
    grupo = get_object_or_404(Group, id=grupo_id)
    perfil, created = GroupProfile.objects.get_or_create(group=grupo)

    if request.method == 'POST':
        form = GroupForm(request.POST)
        if form.is_valid():
            grupo.name = form.cleaned_data['name']
            grupo.save()
            perfil.is_active = form.cleaned_data['is_active']
            perfil.finalidade = form.cleaned_data['finalidade']
            perfil.save()
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'redirect_url': reverse('accounts:lista_grupos')})
            return redirect('accounts:lista_grupos')
    else:
        form = GroupForm(initial={
            'name': grupo.name,
            'is_active': perfil.is_active,
            'finalidade': perfil.finalidade
        })

    return render_ajax_or_base(request, 'partials/accounts/editar_grupo.html', {'form': form, 'grupo': grupo})

@login_required
@user_passes_test(is_super_or_group_admin)
def confirmar_exclusao_grupo(request, grupo_id):
    grupo = get_object_or_404(Group, id=grupo_id)
    return render_ajax_or_base(request, 'partials/accounts/confirmar_exclusao_grupo.html', {'grupo': grupo, 'data_tela': 'confirmar_exclusao_grupo'})

@login_required
@require_POST
@user_passes_test(is_super_or_group_admin)
def excluir_grupo(request, grupo_id):
    grupo = get_object_or_404(Group, id=grupo_id)
    grupo.delete()
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'redirect_url': reverse('accounts:lista_grupos')})
    return redirect('accounts:lista_grupos')

@login_required
@require_POST
@user_passes_test(is_super_or_group_admin)
def excluir_grupo_multiplo(request):
    try:
        # Tenta carregar os IDs do corpo da requisição JSON
        data = json.loads(request.body)
        ids = data.get('ids', [])
    except json.JSONDecodeError:
        # Fallback para o método antigo (formulário)
        ids = request.POST.getlist('grupos_selecionados')

    if not ids:
        msg = "Nenhum grupo selecionado para exclusão."
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': msg}, status=400)
        messages.warning(request, msg)
        return redirect('accounts:lista_grupos')

    grupos = Group.objects.filter(id__in=ids)
    count = grupos.count()
    nomes = list(grupos.values_list('name', flat=True))
    grupos.delete()

    msg = f"{count} grupo(s) excluído(s) com sucesso: {', '.join(nomes)}."
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': msg,
            'redirect_url': reverse('accounts:lista_grupos')
        })
        
    messages.success(request, msg)
    return redirect('accounts:lista_grupos')
# === Permissões Gerais e por Grupo ===


@login_required
@user_passes_test(is_super_or_group_admin)
def gerenciar_permissoes_geral(request):
    """
    Página de gerenciamento geral de permissões por grupo ou usuário.
    Permite selecionar e editar permissões associadas a grupos ou usuários,
    com agrupamento por app e tradução via dicionário externo.
    """
    grupos = Group.objects.all()
    usuarios = User.objects.all()
    permissoes = Permission.objects.select_related('content_type').order_by('content_type__app_label', 'codename')

    # 🔤 Tradução das permissões via dicionário externo
    for p in permissoes:
        p.traduzida = PERMISSOES_PT_BR.get(p.name, p.name)

    # 📌 Identifica se foi enviado grupo ou usuário
    grupo_id = request.GET.get('grupo') or request.POST.get('grupo')
    usuario_id = request.GET.get('usuario') or request.POST.get('usuario')
    permissoes_selecionadas = []
    permissoes_ids = []  # ✅ Inicializa para evitar UnboundLocalError

    # 💾 POST = salvar permissões
    if request.method == 'POST':
        permissoes_ids = request.POST.getlist('permissoes')

        if grupo_id:
            grupo = get_object_or_404(Group, id=grupo_id)
            grupo.permissions.set(permissoes_ids)
            permissoes_selecionadas = grupo.permissions.all()

        elif usuario_id:
            usuario = get_object_or_404(User, id=usuario_id)
            usuario.user_permissions.set(permissoes_ids)
            permissoes_selecionadas = usuario.user_permissions.all()

        # 🔁 Retorno AJAX com mensagem
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': 'Permissões atualizadas com sucesso!'})

    # 🔍 GET = carregar permissões já atribuídas
    else:
        if grupo_id:
            grupo = get_object_or_404(Group, id=grupo_id)
            permissoes_selecionadas = grupo.permissions.all()
            permissoes_ids = list(permissoes_selecionadas.values_list("id", flat=True))
            print(">> IDs das permissões do grupo:", permissoes_ids)

        elif usuario_id:
            usuario = get_object_or_404(User, id=usuario_id)
            permissoes_selecionadas = usuario.user_permissions.all()
            permissoes_ids = list(permissoes_selecionadas.values_list("id", flat=True))
            print(">> IDs das permissões do usuário:", permissoes_ids)

    # 📤 Renderização com contexto completo
    return render_ajax_or_base(request, 'partials/accounts/gerenciar_permissoes_geral.html', {
        'grupos': grupos,
        'usuarios': usuarios,
        'permissoes': permissoes,
        'permissoes_selecionadas': permissoes_selecionadas,
        'permissoes_selecionadas_ids': permissoes_ids,
    })


@login_required
@user_passes_test(is_super_or_group_admin)
def gerenciar_permissoes_grupo_view(request, grupo_id):
    """
    🔐 View para gerenciar permissões atribuídas a um grupo específico.

    Exibe permissões agrupadas por app_label, com nomes traduzidos conforme dicionário PERMISSOES_PT_BR.
    Ao submeter o formulário, atualiza as permissões do grupo e retorna JSON (AJAX) ou redireciona.

    Template: partials/accounts/gerenciar_permissoes_grupo.html
    """

    grupo = get_object_or_404(Group, id=grupo_id)

    # 🔠 Nomes amigáveis para os app_labels
    NOMES_APPS = {
        'auth': 'Permissões',
        'admin': 'Administração',
        'sessions': 'Sessões',
        'accounts': 'Usuários',
        'contenttypes': 'Tipos de Conteúdo',
        'empresas': 'Empresas',
        'nota_fiscal': 'Nota Fiscal',
        'produto': 'Produtos',
    }

    permissoes = Permission.objects.select_related('content_type').order_by(
        'content_type__app_label', 'codename'
    )

    permissoes_agrupadas = {}
    nomes_apps_traduzidos = {}

    for p in permissoes:
        app = p.content_type.app_label
        p.traduzida = PERMISSOES_PT_BR.get(p.name, p.name)
        permissoes_agrupadas.setdefault(app, []).append(p)
        if app not in nomes_apps_traduzidos:
            nomes_apps_traduzidos[app] = NOMES_APPS.get(app, app.capitalize())

    # ✅ Processamento de submissão
    if request.method == 'POST':
        permissoes_ids = request.POST.getlist('permissoes')
        grupo.permissions.set(permissoes_ids)

        # 🔁 Resposta AJAX com mensagem + redirecionamento
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': 'Permissões do grupo atualizadas com sucesso!',
                'redirect_url': reverse('accounts:lista_grupos')
            })

        # 🔁 Resposta padrão (caso não seja AJAX)
        return redirect('accounts:lista_grupos')

    # 📊 Permissões já associadas ao grupo (para pré-marcação no template)
    permissoes_grupo = grupo.permissions.all()

    # 📤 Renderiza o template (AJAX ou completo com base.html)
    return render_ajax_or_base(request, 'partials/accounts/gerenciar_permissoes_grupo.html', {
        'grupo': grupo,
        'permissoes_agrupadas': permissoes_agrupadas,
        'permissoes_grupo': permissoes_grupo,
        'nomes_apps_traduzidos': nomes_apps_traduzidos,
    })

@login_required
@user_passes_test(is_super_or_group_admin)
def visualizar_permissoes_grupo_view(request, grupo_id):
    """
    Exibe permissões de um grupo de forma somente leitura.
    """
    grupo = get_object_or_404(Group, id=grupo_id)
    permissoes = Permission.objects.select_related('content_type').order_by('content_type__app_label', 'codename')
    for p in permissoes:
        p.traduzida = PERMISSOES_PT_BR.get(p.name, p.name)

    permissoes_grupo = grupo.permissions.all()

    return render_ajax_or_base(request, 'partials/accounts/visualizar_permissoes_grupo.html', {
        'grupo': grupo,
        'permissoes': permissoes,
        'permissoes_grupo': permissoes_grupo
    })


@login_required
@user_passes_test(is_super_or_group_admin)
def gerenciar_permissoes_grupo_view_selector(request):
    """
    Tela para selecionar grupo e editar permissões.
    """
    grupos = Group.objects.all()
    return render_ajax_or_base(request, 'partials/accounts/selecionar_grupo_permissoes.html', {
        'grupos': grupos
    })


@login_required
@user_passes_test(is_super_or_group_admin)
def seletor_grupo_permissoes(request):
    """
    Alternativa reutilizável de seletor de grupo com renderização AJAX/base.
    """
    grupos = Group.objects.all()
    return render_ajax_or_base(request, 'partials/accounts/selecionar_grupo_permissoes.html', {
        'grupos': grupos
    })

"""Logout Automático"""
from django.contrib.auth import logout
from django.http import JsonResponse

def logout_automatico_view(request):
    logout(request)
    return JsonResponse({'redirect_url': '/login/'})  # ou reverse('accounts:login')

# === RECUPERAÇÃO DE SENHA CUSTOMIZADA ===

from django.contrib.auth.forms import PasswordResetForm
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail


def password_reset_request_view(request):
    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            User = get_user_model()
            try:
                user = User.objects.get(email__iexact=email)
                
                # Lógica de envio (E-mail ou WhatsApp)
                if 'send_email' in request.POST:
                    # Lógica de envio de e-mail padrão do Django
                    opts = {
                        'use_https': request.is_secure(),
                        'token_generator': default_token_generator,
                        'from_email': None, # Usará o DEFAULT_FROM_EMAIL
                        'email_template_name': 'accounts/password_reset_email.html',
                        'subject_template_name': 'accounts/password_reset_subject.txt',
                        'request': request,
                    }
                    form.save(**opts)
                    return redirect('accounts:password_reset_done')

                elif 'send_whatsapp' in request.POST and user.whatsapp:
                    # Lógica de envio para o WhatsApp
                    token = default_token_generator.make_token(user)
                    uid = urlsafe_base64_encode(force_bytes(user.pk))
                    reset_link = request.build_absolute_uri(reverse('accounts:password_reset_confirm', kwargs={'uidb64': uid, 'token': token}))
                    
                    # Chama nossa função placeholder
                    sucesso = enviar_link_whatsapp(user.whatsapp, reset_link)
                    if sucesso:
                        messages.success(request, f"Link de redefinição enviado para o WhatsApp terminado em {user.whatsapp[-4:]}")
                    else:
                        messages.error(request, "Não foi possível enviar o link via WhatsApp. Tente por e-mail.")
                    return redirect('accounts:password_reset')

                # Se chegou aqui, é a primeira vez que o usuário vê a tela de escolha
                # Ofusca o número do WhatsApp para segurança
                whatsapp_ofuscado = f"*****{user.whatsapp[-4:]}" if user.whatsapp else None
                return render(request, 'accounts/password_reset_choose_method.html', {
                    'user_found': True,
                    'whatsapp_number': whatsapp_ofuscado,
                    'email': email,
                    'form': form # Passa o form para poder reenviar com o mesmo email
                })

            except User.DoesNotExist:
                # Usuário não encontrado, mostra a mesma página de sucesso para não revelar e-mails válidos
                return redirect('accounts:password_reset_done')
    else:
        form = PasswordResetForm()

    return render(request, 'accounts/password_reset.html', {'form': form})"""

file_path = "C:/Users/cdbg2/documents/onetech/accounts/views.py"

with open(file_path, "w") as f:
    f.write(corrected_views_content)

print(f"File {file_path} has been overwritten.")
