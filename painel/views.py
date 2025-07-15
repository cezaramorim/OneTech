from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required(login_url='/accounts/login/')
def painel_onetech(request):
    """
    View principal que renderiza o layout base do sistema (base.html).
    O conteúdo será carregado dinamicamente via AJAX dentro da div #main-content.
    """
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'partials/_main_content_wrapper.html')

    return render(request, 'base.html', {
        'content_template': 'partials/home_content.html'  # ✅ Corrigido aqui
    })
