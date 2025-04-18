from django.shortcuts import render

def render_ajax_or_base(request, content_template, context=None, base_template="base.html"):
    """
    Renderiza o template via AJAX ou via base.html se não for requisição AJAX.
    """
    context = context or {}
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return render(request, content_template, context)
    context["content_template"] = content_template
    return render(request, base_template, context)
