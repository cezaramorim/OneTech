# common/mixins.py
from django.shortcuts import render
from django.core.exceptions import ImproperlyConfigured

class AjaxListMixin:
    """
    Renderiza uma página completa em uma carga normal (GET) e um template
    parcial em requisições AJAX de filtro/paginação/ordenação.
    """
    template_page = None
    template_partial = None

    def render_list(self, request, context):
        # A requisição é AJAX e contém parâmetros de query? (Ex: filtro, paginação)
        # Isso diferencia a carga inicial via AJAX (sem params) de uma ação de filtro.
        is_ajax_action = (
            request.headers.get('x-requested-with') == 'XMLHttpRequest' and
            len(request.GET) > 0
        )

        template_name = self.template_partial if is_ajax_action else self.template_page

        if not template_name or not self.template_page or not self.template_partial:
            raise ImproperlyConfigured(
                "AjaxListMixin requer que 'template_page' e 'template_partial' sejam definidos."
            )
        
        # Para a carga inicial via AJAX, usa-se render_ajax_or_base (ou similar) na view.
        # Este mixin é para a resposta da AÇÃO de filtro/paginação.
        # A lógica na view principal deve ser:
        # if is_ajax_action: return render(partial)
        # else: return render_ajax_or_base(page)
        # O mixin simplifica isso.

        return render(request, template_name, context)
