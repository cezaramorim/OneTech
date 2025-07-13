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

# ✅ Verificação de superusuário ou admin
def is_super_or_group_admin(user):
    return user.is_superuser or user.groups.filter(name__iexact='admin').exists()

# 🔤 Dicionário de traduções de permissões para português
PERMISSOES_PT_BR = {
    # Traduzir app_labels
    "auth": "Usuários e Grupos",
    "accounts": "Gerenciamento de Contas",
    "admin": "Administração",
    "contenttypes": "Tipos de Conteúdo",
    "sessions": "Sessões",
    "empresas": "Empresas",
    "fiscal": "Fiscal",
    "nota_fiscal": "Nota Fiscal",
    "produto": "Produtos",
    
    # 👥 Usuários
    'add_user': 'Adicionar Usuário',
    'change_user': 'Editar Usuário',
    'delete_user': 'Excluir Usuário',
    'view_user': 'Visualizar Usuário',
    "Can add user": "Adicionar usuário",
    "Can change user": "Editar usuário",
    "Can delete user": "Excluir usuário",
    "Can view user": "Visualizar usuário",
    "Can add Usuário": "Adicionar Usuário",
    "Can change Usuário": "Editar Usuário",
    "Can delete Usuário": "Excluir Usuário",
    "Can view Usuário": "Visualizar Usuário",
    "Can add group profile": "Adicionar perfil de grupo",
    "Can change group profile": "Editar perfil de grupo",
    "Can delete group profile": "Excluir perfil de grupo",
    "Can view group profile": "Visualizar perfil de grupo",

    # 🛡️ Grupos
    'add_group': 'Adicionar Grupo',
    'change_group': 'Editar Grupo',
    'delete_group': 'Excluir Grupo',
    'view_group': 'Visualizar Grupo',
    "Can add group": "Adicionar grupo",
    "Can change group": "Editar grupo",
    "Can delete group": "Excluir grupo",
    "Can view group": "Visualizar grupo",

    # 🔐 Permissões
    'add_permission': 'Adicionar Permissão',
    'change_permission': 'Editar Permissão',
    'delete_permission': 'Excluir Permissão',
    'view_permission': 'Visualizar Permissão',
    "Can add permission": "Adicionar permissão",
    "Can change permission": "Editar permissão",
    "Can delete permission": "Excluir permissão",
    "Can view permission": "Visualizar permissão",

    # 🏢 Empresas
    "Can add empresa": "Adicionar empresa",
    "Can change empresa": "Editar empresa",
    "Can delete empresa": "Excluir empresa",
    "Can view empresa": "Visualizar empresa",
    "Can add empresa avancada": "Adicionar empresa avançada",
    "Can change empresa avancada": "Editar empresa avançada",
    "Can delete empresa avancada": "Excluir empresa avançada",
    "Can view empresa avancada": "Visualizar empresa avançada",

    # 🗂️ Categorias de Empresa
    "Can add categoria empresa": "Adicionar categoria de empresa",
    "Can change categoria empresa": "Editar categoria de empresa",
    "Can delete categoria empresa": "Excluir categoria de empresa",
    "Can view categoria empresa": "Visualizar categoria de empresa",

    # 📑 Log de Ações
    "Can add log entry": "Adicionar registro de log",
    "Can change log entry": "Editar registro de log",
    "Can delete log entry": "Excluir registro de log",
    "Can view log entry": "Visualizar registro de log",

    # 🔠 Tipos de Conteúdo
    "Can add content type": "Adicionar tipo de conteúdo",
    "Can change content type": "Editar tipo de conteúdo",
    "Can delete content type": "Excluir tipo de conteúdo",
    "Can view content type": "Visualizar tipo de conteúdo",

    # 🧾 Nota Fiscal
    "Can add Nota Fiscal": "Adicionar Nota Fiscal",
    "Can change Nota Fiscal": "Editar Nota Fiscal",
    "Can delete Nota Fiscal": "Excluir Nota Fiscal",
    "Can view Nota Fiscal": "Visualizar Nota Fiscal",
    "Can add item nota fiscal": "Adicionar item de nota fiscal",
    "Can change item nota fiscal": "Editar item de nota fiscal",
    "Can delete item nota fiscal": "Excluir item de nota fiscal",
    "Can view item nota fiscal": "Visualizar item de nota fiscal",
    "Can add Duplicata da Nota Fiscal": "Adicionar Duplicata da Nota Fiscal",
    "Can change Duplicata da Nota Fiscal": "Editar Duplicata da Nota Fiscal",
    "Can delete Duplicata da Nota Fiscal": "Excluir Duplicata da Nota Fiscal",
    "Can view Duplicata da Nota Fiscal": "Visualizar Duplicata da Nota Fiscal",
    "Can add Transporte da Nota Fiscal": "Adicionar Transporte da Nota Fiscal",
    "Can change Transporte da Nota Fiscal": "Editar Transporte da Nota Fiscal",
    "Can delete Transporte da Nota Fiscal": "Excluir Transporte da Nota Fiscal",
    "Can view Transporte da Nota Fiscal": "Visualizar Transporte da Nota Fiscal",

    # 📦 Produtos
    "Can add produto": "Adicionar produto",
    "Can change produto": "Editar produto",
    "Can delete produto": "Excluir produto",
    "Can view produto": "Visualizar produto",
    "Can add entrada produto": "Adicionar entrada de produto",
    "Can change entrada produto": "Editar entrada de produto",
    "Can delete entrada produto": "Excluir entrada de produto",
    "Can view entrada produto": "Visualizar entrada de produto",
    "Can add ncm": "Adicionar NCM",
    "Can change ncm": "Editar NCM",
    "Can delete ncm": "Excluir NCM",
    "Can view ncm": "Visualizar NCM",
    "Can add categoria produto": "Adicionar categoria de produto",
    "Can change categoria produto": "Editar categoria de produto",
    "Can delete categoria produto": "Excluir categoria de produto",
    "Can view categoria produto": "Visualizar categoria de produto",
    "Can add unidade medida": "Adicionar unidade de medida",
    "Can change unidade medida": "Editar unidade de medida",
    "Can delete unidade medida": "Excluir unidade de medida",
    "Can view unidade medida": "Visualizar unidade de medida",
    "Can add detalhes fiscais produto": "Adicionar detalhes fiscais do produto",
    "Can change detalhes fiscais produto": "Editar detalhes fiscais do produto",
    "Can delete detalhes fiscais produto": "Excluir detalhes fiscais do produto",
    "Can view detalhes fiscais produto": "Visualizar detalhes fiscais do produto",

    # 🕒 Sessões
    "Can add session": "Adicionar sessão",
    "Can change session": "Editar sessão",
    "Can delete session": "Excluir sessão",
    "Can view session": "Visualizar sessão",

    # 🧾 Fiscal
    "Can add CFOP": "Adicionar CFOP",
    "Can change CFOP": "Editar CFOP",
    "Can delete CFOP": "Excluir CFOP",
    "Can view CFOP": "Visualizar CFOP",
    "Can add CSOSN": "Adicionar CSOSN",
    "Can change CSOSN": "Editar CSOSN",
    "Can delete CSOSN": "Excluir CSOSN",
    "Can view CSOSN": "Visualizar CSOSN",
    "Can add CST": "Adicionar CST",
    "Can change CST": "Editar CST",
    "Can delete CST": "Excluir CST",
    "Can view CST": "Visualizar CST",
    "Can add Natureza de Operação": "Adicionar Natureza de Operação",
    "Can change Natureza de Operação": "Editar Natureza de Operação",
    "Can delete Natureza de Operação": "Excluir Natureza de Operação",
    "Can view Natureza de Operação": "Visualizar Natureza de Operação",
}