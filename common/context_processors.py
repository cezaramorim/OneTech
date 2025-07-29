# common/context_processors.py
from django.urls import reverse, NoReverseMatch
from common.menu_config import MENU_ITEMS

def _get_visible_menu(user, menu_structure):
    visible_menu = []
    for item in menu_structure:
        item_copy = item.copy()
        
        # 1. Processar filhos recursivamente
        # Primeiro, filtramos os filhos para ver quais são visíveis.
        has_visible_children = False
        if 'children' in item_copy:
            visible_children = _get_visible_menu(user, item_copy['children'])
            if visible_children:
                item_copy['children'] = visible_children
                has_visible_children = True
            else:
                item_copy['children'] = [] # Remove children if none are visible

        # 2. Determinar visibilidade do item atual
        # Um item é visível se:
        # a) Ele tem uma URL direta E o usuário tem as permissões necessárias para essa URL.
        # OU
        # b) Ele NÃO tem uma URL direta (é um item de agrupamento/submenu) E possui filhos visíveis.
        
        is_direct_link_item = 'url_name' in item_copy and item_copy['url_name'] != '#'
        
        item_should_be_visible = False

        if is_direct_link_item:
            # Se for um link direto, verifica suas próprias permissões
            has_required_perms_for_self = 'required_perms' not in item_copy or user.has_perms(item_copy['required_perms'])
            if has_required_perms_for_self:
                item_should_be_visible = True
        else: # Este é um item de agrupamento (sem url_name direto ou url_name é '#')
            # Itens de agrupamento são visíveis apenas se tiverem filhos visíveis
            if has_visible_children:
                item_should_be_visible = True

        if item_should_be_visible:
            # 3. Resolver URL se for um link direto
            if is_direct_link_item:
                try:
                    item_copy['url'] = reverse(item_copy['url_name'])
                except NoReverseMatch:
                    item_copy['url'] = '#' # Fallback para URLs inválidas
            # Para itens de agrupamento sem url_name, não precisamos definir 'url' aqui,
            # pois o template usa data-bs-target para o colapso.

            visible_menu.append(item_copy)
                
    return visible_menu

def dynamic_menu(request):
    if not request.user.is_authenticated:
        return {'dynamic_menu_items': []}
    
    # Construir o menu visível para o usuário
    visible_menu_items = _get_visible_menu(request.user, MENU_ITEMS)
    
    return {'dynamic_menu_items': visible_menu_items}
