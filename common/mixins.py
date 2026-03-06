from django.core.exceptions import ImproperlyConfigured
from django.shortcuts import render

from common.utils import render_ajax_or_base


class AjaxListMixin:
    """
    Renderiza uma pagina completa em carga normal e apenas o partial
    em acoes AJAX de filtro, paginacao ou ordenacao.
    """

    template_page = None
    template_partial = None

    def render_list(self, request, context):
        is_ajax_action = (
            request.headers.get('x-requested-with') == 'XMLHttpRequest'
            and len(request.GET) > 0
        )

        if not self.template_page or not self.template_partial:
            raise ImproperlyConfigured(
                "AjaxListMixin requer que 'template_page' e 'template_partial' sejam definidos."
            )

        if is_ajax_action:
            return render(request, self.template_partial, context)

        return render_ajax_or_base(request, self.template_page, context)
