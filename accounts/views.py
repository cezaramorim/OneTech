from accounts.utils.permissions_dict import PERMISSOES_PT_BR
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import Permission, Group
from django.http import JsonResponse
from django.contrib import messages
from django.urls import reverse
from django.views.decorators.http import require_POST
from django import forms
from .forms import SignUpForm, EditUserForm
from .models import User

# 🔁 Renderizador AJAX ou base
def render_ajax_or_base(request, partial_template, context):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, partial_template, context)
    return render(request, 'base.html', {**context, 'content_template': partial_template})

# ✅ Verificação de superusuário ou admin
def is_super_or_group_admin(user):
    return user.is_superuser or user.groups.filter(name__iexact='admin').exists()

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

from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.urls import reverse

def login_view(request):
    error = None

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

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
def lista_usuarios(request):
    usuarios = User.objects.all()
    template = 'partials/accounts/lista_usuarios.html' if request.headers.get('x-requested-with') == 'XMLHttpRequest' else 'base.html'
    context = {'usuarios': usuarios} if 'partials' in template else {'usuarios': usuarios, 'content_template': 'partials/accounts/lista_usuarios.html'}
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
                return JsonResponse({'redirect_url': reverse('accounts:lista_usuarios')})
            return redirect('accounts:lista_usuarios')

    # ✅ Aqui está o ponto importante
    contexto = {
        'form': form,
        'usuario': usuario,
        'grupo_atual': grupo_atual,
        'grupos': grupos
    }

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'partials/accounts/editar_usuario.html', contexto)

    return render(request, 'base.html', {
        'content_template': 'partials/accounts/editar_usuario.html',
        **contexto
    })

@login_required
@require_POST
@user_passes_test(is_super_or_group_admin)
def excluir_usuario_multiplo(request):
    ids = request.POST.getlist('usuarios_selecionados')
    if not ids:
        msg = "Nenhum usuário selecionado para exclusão."
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': msg}, status=400)
        messages.warning(request, msg)
        return redirect('accounts:lista_usuarios')

    usuarios = User.objects.filter(id__in=ids)
    nomes = [u.get_full_name() or u.username for u in usuarios]
    usuarios.delete()

    msg = f"{len(nomes)} usuário(s) excluído(s) com sucesso: {', '.join(nomes)}."
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'message': msg})
    messages.success(request, msg)
    return redirect('accounts:lista_usuarios')

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
def editar_permissoes_view(request, usuario_id):
    usuario = get_object_or_404(User, id=usuario_id)
    todas_permissoes = Permission.objects.all()
    permissoes_usuario = usuario.user_permissions.all()

    if request.method == 'POST':
        permissoes_ids = request.POST.getlist('permissoes')
        usuario.user_permissions.set(permissoes_ids)
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'redirect_url': reverse('accounts:selecionar_usuario_permissoes')})
        return redirect('accounts:selecionar_usuario_permissoes')

    return render_ajax_or_base(
        request,
        'partials/accounts/editar_permissoes.html',
        {
            'usuario': usuario,
            'permissoes_usuario': permissoes_usuario,
            'todas_permissoes': todas_permissoes
        }
    )
# === Grupos ===

class GrupoForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ['name']
        labels = {'name': 'Nome do Grupo'}
        widgets = {'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome do grupo'})}

@login_required
@user_passes_test(is_super_or_group_admin)
def lista_grupos(request):
    grupos = Group.objects.all()
    return render_ajax_or_base(
        request,
        'partials/accounts/lista_grupos.html',
        {'grupos': grupos}
    )

@login_required
@user_passes_test(is_super_or_group_admin)
def cadastrar_grupo(request):
    form = GrupoForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'redirect_url': reverse('accounts:lista_grupos')})
        return redirect('accounts:lista_grupos')
    return render_ajax_or_base(request, 'partials/accounts/cadastrar_grupo.html', {'form': form})

@login_required
@user_passes_test(is_super_or_group_admin)
def editar_grupo(request, grupo_id):
    grupo = get_object_or_404(Group, id=grupo_id)
    if request.method == 'POST':
        novo_nome = request.POST.get('nome')
        if novo_nome:
            grupo.name = novo_nome
            grupo.save()
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'redirect_url': reverse('accounts:lista_grupos')})
            return redirect('accounts:lista_grupos')
    return render_ajax_or_base(request, 'partials/accounts/editar_grupo.html', {'grupo': grupo})

@login_required
@user_passes_test(is_super_or_group_admin)
def confirmar_exclusao_grupo(request, grupo_id):
    grupo = get_object_or_404(Group, id=grupo_id)
    return render_ajax_or_base(request, 'partials/accounts/confirmar_exclusao_grupo.html', {'grupo': grupo})

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
    ids = request.POST.getlist('grupos_selecionados')
    if not ids:
        msg = "Nenhum grupo selecionado para exclusão."
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': msg}, status=400)
        messages.warning(request, msg)
        return redirect('accounts:lista_grupos')

    grupos = Group.objects.filter(id__in=ids)
    nomes = [g.name for g in grupos]
    grupos.delete()

    msg = f"{len(nomes)} grupo(s) excluído(s) com sucesso: {', '.join(nomes)}."
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'message': msg})
    messages.success(request, msg)
    return redirect('accounts:lista_grupos')
# === Permissões Gerais e por Grupo ===

@login_required
@user_passes_test(is_super_or_group_admin)
def gerenciar_permissoes_geral(request):
    """
    Página de gerenciamento geral de permissões por grupo ou usuário.
    """
    grupos = Group.objects.all()
    usuarios = User.objects.all()
    permissoes = Permission.objects.select_related('content_type').order_by('content_type__app_label', 'codename')

    # Tradução de permissões
    for p in permissoes:
        p.traduzida = PERMISSOES_PT_BR.get(p.name, p.name)

    # Identifica se é grupo ou usuário
    grupo_id = request.GET.get('grupo') or request.POST.get('grupo')
    usuario_id = request.GET.get('usuario') or request.POST.get('usuario')
    permissoes_selecionadas = []

    # POST = salvar permissões
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

        # Retorno AJAX (JsonResponse)
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': 'Permissões atualizadas com sucesso!'})

    # GET = carregar permissões selecionadas
    else:
        if grupo_id:
            grupo = get_object_or_404(Group, id=grupo_id)
            permissoes_selecionadas = grupo.permissions.all()

        elif usuario_id:
            usuario = get_object_or_404(User, id=usuario_id)
            permissoes_selecionadas = usuario.user_permissions.all()

    return render_ajax_or_base(request, 'partials/accounts/gerenciar_permissoes_geral.html', {
        'grupos': grupos,
        'usuarios': usuarios,
        'permissoes': permissoes,
        'permissoes_selecionadas': permissoes_selecionadas,
    })



@login_required
@user_passes_test(is_super_or_group_admin)
def gerenciar_permissoes_grupo_view(request, grupo_id):
    """
    Página de edição de permissões de um grupo específico.
    """
    grupo = get_object_or_404(Group, id=grupo_id)
    permissoes = Permission.objects.select_related('content_type').order_by('content_type__app_label', 'codename')
    for p in permissoes:
        p.traduzida = PERMISSOES_PT_BR.get(p.name, p.name)

    if request.method == 'POST':
        permissoes_ids = request.POST.getlist('permissoes')
        grupo.permissions.set(permissoes_ids)
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': 'Permissões do grupo atualizadas com sucesso!'})
        return redirect('accounts:lista_grupos')

    permissoes_grupo = grupo.permissions.all()

    return render_ajax_or_base(request, 'partials/accounts/gerenciar_permissoes_grupo.html', {
        'grupo': grupo,
        'permissoes': permissoes,
        'permissoes_grupo': permissoes_grupo
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
