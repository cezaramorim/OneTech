from django.shortcuts import render, redirect
from django.contrib import messages

from accounts.utils.decorators import login_required_json, permission_required_json


@login_required_json
@permission_required_json('painel.view_dashboard', raise_exception=True)
def painel_onetech(request):
    """
    View principal que renderiza o layout base do sistema (base.html).
    O conteudo sera carregado dinamicamente via AJAX dentro da div #main-content.
    """
    if request.GET.get('admin_restrito') == '1':
        messages.error(request, 'Area restrita. Entre em contato com o suporte tecnico.')
        return redirect('painel:home')

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'partials/_main_content_wrapper.html', {'data_page': 'home', 'data_tela': 'home'})

    return render(request, 'base.html', {
        'content_template': 'partials/home_content.html',
        'data_page': 'home',
        'data_tela': 'home'
    })
