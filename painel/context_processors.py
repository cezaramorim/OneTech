# painel/context_processors.py

def definir_data_tela(request):
    path = request.path

    if "/accounts/grupos/ver-permissoes/" in path:
        tela = "visualizar-permissoes-grupo"
    elif "/accounts/grupos/" in path and "/permissoes/" in path:
        tela = "gerenciar-permissoes-grupo"
    elif "/accounts/permissoes/por-grupo/" in path:
        tela = "gerenciar-permissoes-grupo-selector"
    elif "/accounts/grupos/" in path:
        tela = "lista-grupos"
    elif "/empresas/nova-avancada/" in path:
        tela = "empresa_avancada"
    else:
        try:
            tela = request.resolver_match.url_name
        except:
            tela = ""

    return {"data_tela": tela}
