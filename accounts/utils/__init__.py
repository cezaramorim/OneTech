# accounts/utils/__init__.py

def is_super_or_group_admin(user):
    """Verifica se o usuário é superusuário ou pertence a um grupo chamado 'Admin'."""
    if not user.is_authenticated:
        return False
    return user.is_superuser or user.groups.filter(name__iexact='admin').exists()


PERMISSOES_PT_BR = {
    # accounts
    "Can add group profile": "Adicionar perfil de grupo",
    "Can change group profile": "Alterar perfil de grupo",
    "Can delete group profile": "Excluir perfil de grupo",
    "Can view group profile": "Visualizar perfil de grupo",
    "Can add Usuário": "Adicionar Usuário",
    "Can change Usuário": "Alterar Usuário",
    "Can delete Usuário": "Excluir Usuário",
    "Can view Usuário": "Visualizar Usuário",

    # empresas
    "Can add categoria empresa": "Adicionar categoria de empresa",
    "Can change categoria empresa": "Alterar categoria de empresa",
    "Can delete categoria empresa": "Excluir categoria de empresa",
    "Can view categoria empresa": "Visualizar categoria de empresa",
    "Can add empresa": "Adicionar empresa",
    "Can change empresa": "Alterar empresa",
    "Can delete empresa": "Excluir empresa",
    "Can view empresa": "Visualizar empresa",

    # fiscal
    "Can add CFOP": "Adicionar CFOP",
    "Can change CFOP": "Alterar CFOP",
    "Can delete CFOP": "Excluir CFOP",
    "Can view CFOP": "Visualizar CFOP",
    "Can add CSOSN": "Adicionar CSOSN",
    "Can change CSOSN": "Alterar CSOSN",
    "Can delete CSOSN": "Excluir CSOSN",
    "Can view CSOSN": "Visualizar CSOSN",
    "Can add CST": "Adicionar CST",
    "Can change CST": "Alterar CST",
    "Can delete CST": "Excluir CST",
    "Can view CST": "Visualizar CST",
    "Can add Natureza de Operação": "Adicionar Natureza de Operação",
    "Can change Natureza de Operação": "Alterar Natureza de Operação",
    "Can delete Natureza de Operação": "Excluir Natureza de Operação",
    "Can view Natureza de Operação": "Visualizar Natureza de Operação",

    # nota_fiscal
    "Can add Duplicata da Nota Fiscal": "Adicionar Duplicata da Nota Fiscal",
    "Can change Duplicata da Nota Fiscal": "Alterar Duplicata da Nota Fiscal",
    "Can delete Duplicata da Nota Fiscal": "Excluir Duplicata da Nota Fiscal",
    "Can view Duplicata da Nota Fiscal": "Visualizar Duplicata da Nota Fiscal",
    "Can add item nota fiscal": "Adicionar item da nota fiscal",
    "Can change item nota fiscal": "Alterar item da nota fiscal",
    "Can delete item nota fiscal": "Excluir item da nota fiscal",
    "Can view item nota fiscal": "Visualizar item da nota fiscal",
    "Can add Nota Fiscal": "Adicionar Nota Fiscal",
    "Can change Nota Fiscal": "Alterar Nota Fiscal",
    "Can delete Nota Fiscal": "Excluir Nota Fiscal",
    "Can view Nota Fiscal": "Visualizar Nota Fiscal",
    "Can add Transporte da Nota Fiscal": "Adicionar Transporte da Nota Fiscal",
    "Can change Transporte da Nota Fiscal": "Alterar Transporte da Nota Fiscal",
    "Can delete Transporte da Nota Fiscal": "Excluir Transporte da Nota Fiscal",
    "Can view Transporte da Nota Fiscal": "Visualizar Transporte da Nota Fiscal",

    # producao
    "Can add Alimentação Diária": "Adicionar Alimentação Diária",
    "Can change Alimentação Diária": "Alterar Alimentação Diária",
    "Can delete Alimentação Diária": "Excluir Alimentação Diária",
    "Can view Alimentação Diária": "Visualizar Alimentação Diária",
    "Can add Atividade": "Adicionar Atividade",
    "Can change Atividade": "Alterar Atividade",
    "Can delete Atividade": "Excluir Atividade",
    "Can view Atividade": "Visualizar Atividade",
    "Can add Curva de Crescimento": "Adicionar Curva de Crescimento",
    "Can change Curva de Crescimento": "Alterar Curva de Crescimento",
    "Can delete Curva de Crescimento": "Excluir Curva de Crescimento",
    "Can view Curva de Crescimento": "Visualizar Curva de Crescimento",
    "Can add Detalhe da Curva de Crescimento": "Adicionar Detalhe da Curva",
    "Can change Detalhe da Curva de Crescimento": "Alterar Detalhe da Curva",
    "Can delete Detalhe da Curva de Crescimento": "Excluir Detalhe da Curva",
    "Can view Detalhe da Curva de Crescimento": "Visualizar Detalhe da Curva",
    "Can add Evento de Manejo": "Adicionar Evento de Manejo",
    "Can change Evento de Manejo": "Alterar Evento de Manejo",
    "Can delete Evento de Manejo": "Excluir Evento de Manejo",
    "Can view Evento de Manejo": "Visualizar Evento de Manejo",
    "Can add Fase de Produção": "Adicionar Fase de Produção",
    "Can change Fase de Produção": "Alterar Fase de Produção",
    "Can delete Fase de Produção": "Excluir Fase de Produção",
    "Can view Fase de Produção": "Visualizar Fase de Produção",
    "Can add Linha de Produção": "Adicionar Linha de Produção",
    "Can change Linha de Produção": "Alterar Linha de Produção",
    "Can delete Linha de Produção": "Excluir Linha de Produção",
    "Can view Linha de Produção": "Visualizar Linha de Produção",
    "Can add Lote": "Adicionar Lote",
    "Can change Lote": "Alterar Lote",
    "Can delete Lote": "Excluir Lote",
    "Can view Lote": "Visualizar Lote",
    "Can add Malha": "Adicionar Malha",
    "Can change Malha": "Alterar Malha",
    "Can delete Malha": "Excluir Malha",
    "Can view Malha": "Visualizar Malha",
    "Can add Status do Tanque": "Adicionar Status do Tanque",
    "Can change Status do Tanque": "Alterar Status do Tanque",
    "Can delete Status do Tanque": "Excluir Status do Tanque",
    "Can view Status do Tanque": "Visualizar Status do Tanque",
    "Can add Tanque": "Adicionar Tanque",
    "Can change Tanque": "Alterar Tanque",
    "Can delete Tanque": "Excluir Tanque",
    "Can view Tanque": "Visualizar Tanque",
    "Can add Tipo de Tanque": "Adicionar Tipo de Tanque",
    "Can change Tipo de Tanque": "Alterar Tipo de Tanque",
    "Can delete Tipo de Tanque": "Excluir Tipo de Tanque",
    "Can view Tipo de Tanque": "Visualizar Tipo de Tanque",
    "Can add Tipo de Tela": "Adicionar Tipo de Tela",
    "Can change Tipo de Tela": "Alterar Tipo de Tela",
    "Can delete Tipo de Tela": "Excluir Tipo de Tela",
    "Can view Tipo de Tela": "Visualizar Tipo de Tela",
    "Can add Unidade": "Adicionar Unidade",
    "Can change Unidade": "Alterar Unidade",
    "Can delete Unidade": "Excluir Unidade",
    "Can view Unidade": "Visualizar Unidade",

    "Can add Arraçoamento Realizado": "Adicionar Arraçoamento Realizado",
    "Can change Arraçoamento Realizado": "Alterar Arraçoamento Realizado",
    "Can delete Arraçoamento Realizado": "Excluir Arraçoamento Realizado",
    "Can view Arraçoamento Realizado": "Visualizar Arraçoamento Realizado",
    "Can add Sugestão de Arraçoamento": "Adicionar Sugestão de Arraçoamento",
    "Can change Sugestão de Arraçoamento": "Alterar Sugestão de Arraçoamento",
    "Can delete Sugestão de Arraçoamento": "Excluir Sugestão de Arraçoamento",
    "Can view Sugestão de Arraçoamento": "Visualizar Sugestão de Arraçoamento",
    "Can add Histórico Diário do Lote": "Adicionar Histórico Diário do Lote",
    "Can change Histórico Diário do Lote": "Alterar Histórico Diário do Lote",
    "Can delete Histórico Diário do Lote": "Excluir Histórico Diário do Lote",
    "Can view Histórico Diário do Lote": "Visualizar Histórico Diário do Lote",
    "Can add Perfil de Ração": "Adicionar Perfil de Ração",
    "Can change Perfil de Ração": "Alterar Perfil de Ração",
    "Can delete Perfil de Ração": "Excluir Perfil de Ração",
    "Can view Perfil de Ração": "Visualizar Perfil de Ração",

    # produto
    "Can add categoria produto": "Adicionar categoria de produto",
    "Can change categoria produto": "Alterar categoria de produto",
    "Can delete categoria produto": "Excluir categoria de produto",
    "Can view categoria produto": "Visualizar categoria de produto",
    "Can add detalhes fiscais produto": "Adicionar detalhes fiscais do produto",
    "Can change detalhes fiscais produto": "Alterar detalhes fiscais do produto",
    "Can delete detalhes fiscais produto": "Excluir detalhes fiscais do produto",
    "Can view detalhes fiscais produto": "Visualizar detalhes fiscais do produto",
    "Can add entrada produto": "Adicionar entrada de produto",
    "Can change entrada produto": "Alterar entrada de produto",
    "Can delete entrada produto": "Excluir entrada de produto",
    "Can view entrada produto": "Visualizar entrada de produto",
    "Can add ncm": "Adicionar NCM",
    "Can change ncm": "Alterar NCM",
    "Can delete ncm": "Excluir NCM",
    "Can view ncm": "Visualizar NCM",
    "Can add produto": "Adicionar produto",
    "Can change produto": "Alterar produto",
    "Can delete produto": "Excluir produto",
    "Can view produto": "Visualizar produto",
    "Can add unidade medida": "Adicionar unidade de medida",
    "Can change unidade medida": "Alterar unidade de medida",
    "Can delete unidade medida": "Excluir unidade de medida",
    "Can view unidade medida": "Visualizar unidade de medida",
}

ACOES_PERMISSAO_PT_BR = {
    'add': 'Adicionar',
    'change': 'Alterar',
    'delete': 'Excluir',
    'view': 'Visualizar',
}


NOMES_APPS_PT_BR = {
    'accounts': 'Contas e Acesso',
    'control': 'Controle',
    'empresas': 'Empresas',
    'produto': 'Produtos',
    'nota_fiscal': 'Nota Fiscal',
    'fiscal': 'Fiscal',
    'relatorios': 'Relatórios',
    'producao': 'Produção',
}


NOMES_ENTIDADES_PT_BR = {
    'groupprofile': 'Perfil de grupo',
    'user': 'Usuário',
    'tenant': 'Tenant',
}


ORDEM_APPS_PERMISSOES = [
    'accounts',
    'control',
    'empresas',
    'produto',
    'nota_fiscal',
    'fiscal',
    'relatorios',
    'producao',
]


def traduzir_nome_app(app_label):
    return NOMES_APPS_PT_BR.get(app_label, app_label.replace('_', ' ').title())


def ordem_app_permissao(app_label):
    try:
        return ORDEM_APPS_PERMISSOES.index(app_label)
    except ValueError:
        return len(ORDEM_APPS_PERMISSOES)


def _get_model_verbose_name(permission):
    model_class = permission.content_type.model_class()
    if model_class is not None:
        return str(model_class._meta.verbose_name)
    return permission.content_type.model.replace('_', ' ')


def nome_entidade_permissao(permission):
    nome_customizado = NOMES_ENTIDADES_PT_BR.get(permission.content_type.model)
    if nome_customizado:
        return nome_customizado

    nome = _get_model_verbose_name(permission)
    return nome[:1].upper() + nome[1:] if nome else permission.content_type.model.replace('_', ' ').title()


def traduzir_permissao(permission):
    traducao_direta = PERMISSOES_PT_BR.get(permission.name)
    if traducao_direta:
        return traducao_direta

    acao = permission.codename.split('_', 1)[0]
    acao_traduzida = ACOES_PERMISSAO_PT_BR.get(acao)
    if not acao_traduzida:
        return permission.name

    return f'{acao_traduzida} {_get_model_verbose_name(permission)}'


def ordem_acao_permissao(codename):
    acao = codename.split('_', 1)[0]
    ordem = {
        'view': 0,
        'add': 1,
        'change': 2,
        'delete': 3,
    }
    return ordem.get(acao, 99)



