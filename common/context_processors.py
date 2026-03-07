# common/context_processors.py
from django.urls import reverse, NoReverseMatch
from common.menu_config import MENU_ITEMS
from control.utils import is_principal_context

def _get_visible_menu(user, menu_structure):
    visible_menu = []
    for item in menu_structure:
        item_copy = item.copy()
        
        # 1. Processar filhos recursivamente
        has_visible_children = False
        if 'children' in item_copy:
            visible_children = _get_visible_menu(user, item_copy['children'])
            if visible_children:
                item_copy['children'] = visible_children
                has_visible_children = True
            else:
                item_copy.pop('children', None)

        # 2. Verificar permissões do item atual
        has_perms = 'required_perms' not in item_copy or user.has_perms(item_copy['required_perms'])
        is_staff_allowed = not item_copy.get('staff_only') or user.is_staff
        is_superuser_allowed = not item_copy.get('superuser_only') or user.is_superuser

        # 3. Determinar se o item é um link clicável
        is_link = 'url_name' in item_copy or 'url' in item_copy

        # 4. Determinar visibilidade:
        # O item é visível se o usuário tem permissão E (ele é um link clicável OU ele tem filhos visíveis)
        if has_perms and is_staff_allowed and is_superuser_allowed and (is_link or has_visible_children):
            # 5. Resolver a URL
            if 'url' not in item_copy:  # Prioriza a URL hardcoded se ela já existir
                try:
                    # Tenta resolver a URL dinâmica a partir do nome
                    item_copy['url'] = reverse(item_copy.get('url_name', ''))
                except NoReverseMatch:
                    # Se falhar, define como um link morto para indicar um erro de configuração
                    item_copy['url'] = '#'
            
            visible_menu.append(item_copy)
                
    return visible_menu

def dynamic_menu(request):
    if not request.user.is_authenticated:
        return {'dynamic_menu_items': []}
    
    # Construir o menu visível para o usuário
    visible_menu_items = _get_visible_menu(request.user, MENU_ITEMS)
    
    # Se estiver em um contexto de tenant, remove o menu 'Admin'
    if not is_principal_context(request):
        visible_menu_items = [item for item in visible_menu_items if item.get('name') != 'Admin']
    
    return {'dynamic_menu_items': visible_menu_items}
