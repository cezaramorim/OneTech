from django.shortcuts import render

def render_ajax_or_base(request, content_template, context=None, base_template="base.html"):
    """
    Renderiza um template parcial dentro do base.html para requisições normais
    ou apenas o template parcial para requisições AJAX.
    Esta é a versão centralizada e única para todo o projeto.
    """
    context = context or {}
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return render(request, content_template, context)
    context["content_template"] = content_template
    return render(request, base_template, context)
