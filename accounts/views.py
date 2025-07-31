from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import Permission, Group, User
from django.http import JsonResponse
from django.contrib import messages
from common.messages_utils import get_app_messages
from django.urls import reverse
from django.views.decorators.http import require_POST
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth import views as auth_views
from django.contrib.auth.forms import PasswordResetForm
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.template.response import TemplateResponse

from .forms import SignUpForm, EditUserForm, GroupForm
from .models import User, GroupProfile
from accounts.utils import PERMISSOES_PT_BR, is_super_or_group_admin
from common.utils import render_ajax_or_base


# === Autenticação ===
def signup_view(request):
    app_messages = get_app_messages(request)
    form = SignUpForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            user = form.save()
            login(request, user)
            app_messages.success_created(user)
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
    # A verificação do método é importante para segurança
    if request.method == 'POST':
        logout(request)
        
        # Se for uma requisição AJAX, retorna uma resposta JSON
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'redirect_url': reverse('accounts:login')
            })
            
        # Para requisições normais, redireciona como antes
        return redirect('accounts:login')

    # Se não for POST, apenas redireciona para a página de login
    return redirect('accounts:login')

@login_required
def edit_profile_view(request):
    app_messages = get_app_messages(request)
    form = EditUserForm(request.POST or None, instance=request.user, request_user=request.user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        app_messages.success_updated(request.user)

    template = 'partials/accounts/edit_profile.html' if request.headers.get('x-requested-with') == 'XMLHttpRequest' else 'base.html'
    context = {'form': form} if 'partials' in template else {'form': form, 'content_template': 'partials/accounts/edit_profile.html'}
    return render(request, template, context)

@login_required
@user_passes_test(is_super_or_group_admin)
def criar_usuario(request):
    app_messages = get_app_messages(request)
    form = SignUpForm(request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            novo_usuario = form.save()

            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                # ✅ Retorna JSON com sucesso e mensagem
                return JsonResponse({
                    'success': True,
                    'message': app_messages.success_created(novo_usuario), # Mensagem será gerada aqui
                    'redirect_url': reverse('accounts:lista_usuarios')
                })

            # ✅ Comum: exibe mensagem e redireciona
            app_messages.success_created(novo_usuario)
            return redirect('accounts:lista_usuarios')

        else:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                # ❌ Retorna erros e mensagem via JSON
                return JsonResponse({
                    'success': False,
                    'errors': form.errors,
                    'message': app_messages.error('Erro ao criar usuário. Verifique os campos.')
                }, status=400)

            # ❌ Comum: exibe erro e renderiza novamente o formulário
            app_messages.error('Erro ao criar usuário. Verifique os campos.')

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
    app_messages = get_app_messages(request)
    usuario = get_object_or_404(User, id=usuario_id)
    form = EditUserForm(request.POST or None, instance=usuario, request_user=request.user)
    grupos = Group.objects.all()
    grupo_atual = usuario.groups.first()

    if request.method == 'POST':
        if form.is_valid():
            form.save()
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'sucesso': True,
                    'mensagem': app_messages.success_updated(usuario), # Mensagem será gerada aqui
                    'redirect_url': reverse('accounts:lista_usuarios')
                })
            app_messages.success_updated(usuario)
            return redirect('accounts:lista_usuarios')
        else:
            print(f"DEBUG: form.errors: {form.errors}")
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                # ❌ Retorna erros e mensagem via JSON
                return JsonResponse({
                    'sucesso': False,
                    'mensagem': app_messages.error("Erro ao atualizar usuário. Verifique os campos."),
                    'errors': form.errors # Mantém os erros do formulário para o frontend
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
    app_messages = get_app_messages(request)
    try:
        data = json.loads(request.body)
        ids = data.get('ids', [])
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': app_messages.error('Dados inválidos.')}, status=400)

    if not ids:
        return JsonResponse({'success': False, 'message': app_messages.error('Nenhum usuário selecionado para exclusão.')}, status=400)

    usuarios = User.objects.filter(id__in=ids)
    count = usuarios.count()
    usuarios.delete()

    msg = app_messages.success_deleted("usuário(s)", f"{count} selecionado(s)")
    return JsonResponse({
        'success': True,
        'message': msg,
        'redirect_url': reverse('accounts:lista_usuarios')
    })



# === Permissões (Refatorado) ===

def _get_permissoes_context():
    """
    Busca e organiza as permissões do sistema, agrupando por app e traduzindo os nomes.
    Filtra apps irrelevantes para a interface de gerenciamento.
    """
    # Apps a serem excluídos da lista de permissões, pois não são gerenciáveis pela interface
    EXCLUDED_APPS = [
        'admin', 'auth', 'contenttypes', 'sessions', 'authtoken', 
        'django_celery_beat', 'integracao_nfe', 'painel'
    ]
    
    permissoes = Permission.objects.select_related('content_type')                                   .exclude(content_type__app_label__in=EXCLUDED_APPS)                                   .order_by('content_type__app_label', 'codename')

    permissoes_agrupadas = {}
    # Mapeia o app_label para um nome amigável e traduzido
    nomes_apps_traduzidos = {
        'accounts': 'Contas e Acesso',
        'empresas': 'Empresas',
        'produto': 'Produtos',
        'nota_fiscal': 'Nota Fiscal',
        'fiscal': 'Fiscal',
        'relatorios': 'Relatórios'
    }

    for p in permissoes:
        app = p.content_type.app_label
        # Usa o nome traduzido do app, ou o nome capitalizado como fallback
        nome_app_display = nomes_apps_traduzidos.get(app, app.capitalize())
        
        # Traduz o nome da permissão individual
        p.traduzida = PERMISSOES_PT_BR.get(p.name, p.name)
        
        # Agrupa as permissões pelo nome de exibição do app
        if nome_app_display not in permissoes_agrupadas:
            permissoes_agrupadas[nome_app_display] = []
        permissoes_agrupadas[nome_app_display].append(p)
        
    return permissoes_agrupadas

@login_required
@user_passes_test(is_super_or_group_admin)
def gerenciar_permissoes_grupo(request, group_id):
    app_messages = get_app_messages(request)
    grupo = get_object_or_404(Group, id=group_id)
    permissoes_agrupadas = _get_permissoes_context()

    if request.method == 'POST':
        permissoes_ids = request.POST.getlist('permissoes')
        print(f"DEBUG: gerenciar_permissoes_grupo - permissoes_ids recebidos no POST: {permissoes_ids}")
        grupo.permissions.set(permissoes_ids)
        if not request.headers.get('x-requested-with') == 'XMLHttpRequest':
            app_messages.success_updated(grupo, custom_message=f'Permissões do grupo "{grupo.name}" atualizadas com sucesso!')
        
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': app_messages.success_updated(grupo, custom_message=f'Permissões do grupo "{grupo.name}" atualizadas com sucesso!'),
                'redirect_url': reverse('accounts:lista_grupos')
            })
        return redirect('accounts:lista_grupos')

    permissoes_grupo_ids = set(grupo.permissions.values_list('id', flat=True))
    print(f"DEBUG: gerenciar_permissoes_grupo - permissoes_entidade_ids (GET/Após POST): {permissoes_grupo_ids}")

    context = {
        'entidade': grupo,
        'permissoes_agrupadas': permissoes_agrupadas,
        'permissoes_entidade_ids': permissoes_grupo_ids,
        'tipo_entidade': 'Grupo',
        'data_page': 'gerenciar_permissoes'
    }
    return render_ajax_or_base(request, 'partials/accounts/gerenciar_permissoes.html', context)

@login_required
@user_passes_test(is_super_or_group_admin)
def gerenciar_permissoes_usuario(request, user_id):
    app_messages = get_app_messages(request)
    usuario = get_object_or_404(get_user_model(), id=user_id)
    permissoes_agrupadas = _get_permissoes_context()

    if request.method == 'POST':
        permissoes_ids = request.POST.getlist('permissoes')
        print(f"DEBUG: gerenciar_permissoes_usuario - permissoes_ids recebidos no POST: {permissoes_ids}")
        usuario.user_permissions.set(permissoes_ids)
        if not request.headers.get('x-requested-with') == 'XMLHttpRequest':
            app_messages.success_updated(usuario, custom_message=f'Permissões do usuário "{usuario.get_full_name()}" atualizadas com sucesso!')
        
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': app_messages.success_updated(usuario, custom_message=f'Permissões do usuário "{usuario.get_full_name() or usuario.username}" atualizadas com sucesso!'),
                'redirect_url': reverse('accounts:lista_usuarios')
            })
        return redirect('accounts:lista_usuarios')

    permissoes_usuario_ids = set(usuario.user_permissions.values_list('id', flat=True))
    print(f"DEBUG: gerenciar_permissoes_usuario - permissoes_entidade_ids (GET/Após POST): {permissoes_usuario_ids}")
    print(f"DEBUG: gerenciar_permissoes_usuario - usuario.first_name: {usuario.first_name}, usuario.last_name: {usuario.last_name}")

    context = {
        'entidade': usuario,
        'permissoes_agrupadas': permissoes_agrupadas,
        'permissoes_entidade_ids': permissoes_usuario_ids,
        'tipo_entidade': 'Usuário',
        'data_page': 'gerenciar_permissoes'
    }
    return render_ajax_or_base(request, 'partials/accounts/gerenciar_permissoes.html', context)



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
    app_messages = get_app_messages(request)
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
                return JsonResponse({'redirect_url': reverse('accounts:lista_grupos'), 'message': app_messages.success_created(group)})
            app_messages.success_created(group)
            return redirect('accounts:lista_grupos')
        else:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'errors': form.errors, 'message': app_messages.error('Erro ao cadastrar grupo. Verifique os campos.')}, status=400)
            app_messages.error('Erro ao cadastrar grupo. Verifique os campos.')
    else:
        form = GroupForm()
    return render_ajax_or_base(request, 'partials/accounts/cadastrar_grupo.html', {'form': form})

@login_required
@user_passes_test(is_super_or_group_admin)
def editar_grupo(request, grupo_id):
    app_messages = get_app_messages(request)
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
                return JsonResponse({'redirect_url': reverse('accounts:lista_grupos'), 'message': app_messages.success_updated(grupo)})
            app_messages.success_updated(grupo)
            return redirect('accounts:lista_grupos')
        else:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'errors': form.errors, 'message': app_messages.error('Erro ao atualizar grupo. Verifique os campos.')}, status=400)
            app_messages.error('Erro ao atualizar grupo. Verifique os campos.')
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
    app_messages = get_app_messages(request)
    grupo = get_object_or_404(Group, id=grupo_id)
    grupo.delete()
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'redirect_url': reverse('accounts:lista_grupos'), 'message': app_messages.success_deleted("grupo", grupo.name)})
    app_messages.success_deleted("grupo", grupo.name)
    return redirect('accounts:lista_grupos')

@login_required
@require_POST
@user_passes_test(is_super_or_group_admin)
def excluir_grupo_multiplo(request):
    app_messages = get_app_messages(request)
    try:
        # Tenta carregar os IDs do corpo da requisição JSON
        data = json.loads(request.body)
        ids = data.get('ids', [])
    except json.JSONDecodeError:
        # Fallback para o método antigo (formulário)
        ids = request.POST.getlist('grupos_selecionados')

    if not ids:
        msg = app_messages.error("Nenhum grupo selecionado para exclusão.")
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': msg}, status=400)
        app_messages.warning(msg)
        return redirect('accounts:lista_grupos')

    grupos = Group.objects.filter(id__in=ids)
    count = grupos.count()
    nomes = list(grupos.values_list('name', flat=True))
    grupos.delete()

    msg = app_messages.success_deleted("grupo(s)", f"{count} selecionado(s)")
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': msg,
            'redirect_url': reverse('accounts:lista_grupos')
        })
        
    app_messages.success_deleted("grupo(s)", f"{count} selecionado(s)")
    return redirect('accounts:lista_grupos')


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
                return render_ajax_or_base(request, 'accounts/password_reset_choose_method.html', {
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

    return render_ajax_or_base(request, 'accounts/password_reset.html', {'form': form})

# Custom Django Auth Views for AJAX compatibility
class CustomPasswordResetDoneView(auth_views.PasswordResetDoneView):
    def render_to_response(self, context, **response_kwargs):
        return render_ajax_or_base(self.request, self.template_name, context)

class CustomPasswordResetConfirmView(auth_views.PasswordResetConfirmView):
    def render_to_response(self, context, **response_kwargs):
        return render_ajax_or_base(self.request, self.template_name, context)

class CustomPasswordResetCompleteView(auth_views.PasswordResetCompleteView):
    def render_to_response(self, context, **response_kwargs):
        return render_ajax_or_base(self.request, self.template_name, context)
