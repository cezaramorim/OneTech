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
    "Can add nota fiscal": "Adicionar nota fiscal",
    "Can change nota fiscal": "Editar nota fiscal",
    "Can delete nota fiscal": "Excluir nota fiscal",
    "Can view nota fiscal": "Visualizar nota fiscal",

    "Can add item nota fiscal": "Adicionar item de nota fiscal",
    "Can change item nota fiscal": "Editar item de nota fiscal",
    "Can delete item nota fiscal": "Excluir item de nota fiscal",
    "Can view item nota fiscal": "Visualizar item de nota fiscal",

    "Can add duplicata nota fiscal": "Adicionar duplicata de nota fiscal",
    "Can change duplicata nota fiscal": "Editar duplicata de nota fiscal",
    "Can delete duplicata nota fiscal": "Excluir duplicata de nota fiscal",
    "Can view duplicata nota fiscal": "Visualizar duplicata de nota fiscal",

    "Can add transporte nota fiscal": "Adicionar transporte de nota fiscal",
    "Can change transporte nota fiscal": "Editar transporte de nota fiscal",
    "Can delete transporte nota fiscal": "Excluir transporte de nota fiscal",
    "Can view transporte nota fiscal": "Visualizar transporte de nota fiscal",

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

    # 🕒 Sessões
    "Can add session": "Adicionar sessão",
    "Can change session": "Editar sessão",
    "Can delete session": "Excluir sessão",
    "Can view session": "Visualizar sessão",
}

# ✅ Adicione novas permissões personalizadas aqui conforme necessário.

# Exemplo:
# PERMISSOES_PT_BR['can_do_something_custom'] = 'Pode fazer algo personalizado'
# PERMISSOES_PT_BR['view_dashboard'] = 'Visualizar painel de controle'

def enviar_link_whatsapp(numero_destino, link_redefinicao):
    """
    Envia uma mensagem com o link de redefinição de senha para o WhatsApp.

    Esta é uma função de exemplo (placeholder). Para funcionar, você precisa
    integrá-la com um serviço de API de WhatsApp, como Twilio, Z-API, etc.

    Args:
        numero_destino (str): O número de telefone do destinatário no formato internacional (ex: +5511999999999).
        link_redefinicao (str): A URL completa para redefinir a senha.

    Returns:
        bool: True se a mensagem foi enviada com sucesso, False caso contrário.
    """
    print("--- SIMULAÇÃO DE ENVIO DE WHATSAPP ---")
    print(f"Para: {numero_destino}")
    print(f"Mensagem: Olá! Para redefinir sua senha, acesse: {link_redefinicao}")
    print("--------------------------------------")

    #
    # --- INÍCIO DA ÁREA DE INTEGRAÇÃO ---
    #
    # Substitua o código abaixo pela lógica de envio da sua API de WhatsApp.
    # Exemplo com uma API fictícia:
    #
    # import requests
    #
    # api_url = "https://api.seuprovedor.com/send"
    # api_key = "SUA_CHAVE_DE_API_AQUI"
    # headers = {"Authorization": f"Bearer {api_key}"}
    # data = {
    #     "to": numero_destino,
    #     "message": f"Olá! Para redefinir sua senha, acesse: {link_redefinicao}"
    # }
    #
    # try:
    #     response = requests.post(api_url, headers=headers, json=data)
    #     response.raise_for_status()  # Lança um erro para respostas 4xx/5xx
    #     return True # Sucesso
    # except requests.exceptions.RequestException as e:
    #     print(f"Erro ao enviar WhatsApp: {e}")
    #     return False # Falha
    #
    # --- FIM DA ÁREA DE INTEGRAÇÃO ---
    #

    # Como esta é uma simulação, retornamos True para indicar que o fluxo pode continuar.
    # No ambiente de produção, isso dependerá da resposta da API.
    return True