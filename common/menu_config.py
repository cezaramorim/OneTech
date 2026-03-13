# common/menu_config.py

MENU_ITEMS = [
    {
        'name': 'Admin',
        'icon': '👑',
        'required_perms': ['control.view_admin_menu'],
        'children': [
            {'name': 'Listar Clientes', 'icon': '👥', 'url_name': 'control:tenant_list', 'required_perms': ['control.view_tenant']},
            {'name': 'Novo Cliente', 'icon': '➕', 'url_name': 'control:tenant_create', 'required_perms': ['control.add_tenant']},
            {'name': 'Usuários por Cliente', 'icon': '🔍', 'url_name': 'control:tenant_user_list', 'required_perms': ['accounts.view_user']},
            {'name': 'Painel Django', 'icon': '🔒', 'url': '/admin/', 'is_external': True, 'required_perms': ['control.view_django_admin_link'], 'staff_only': True},
            {'name': 'Central de Migracoes', 'icon': '<i class="bi bi-database-gear"></i>', 'url_name': 'control:central_migracoes', 'superuser_only': True},
        ]
    },
    {
        'name': 'Configurações',
        'icon': '⚙️',
        'children': [
            {'name': 'Emitentes / Filiais', 'icon': '🏢', 'url_name': 'control:lista_emitentes', 'required_perms': ['control.view_emitente']},
            {'name': 'Novo Usuário', 'icon': '👤', 'url_name': 'accounts:criar_usuario', 'required_perms': ['accounts.add_user']},
            {'name': 'Lista de Usuários', 'icon': '👤', 'url_name': 'accounts:lista_usuarios', 'required_perms': ['accounts.view_user']},
            {'name': 'Novo Grupo', 'icon': '🛡️', 'url_name': 'accounts:cadastrar_grupo', 'required_perms': ['auth.add_group']},
            {'name': 'Lista de Grupos', 'icon': '🛡️', 'url_name': 'accounts:lista_grupos', 'required_perms': ['auth.view_group']},
        ]
    },    
    {
        'name': 'Lotes',
        'icon': '🐠',
        'children': [
            {'name': 'Reprocessar Lotes', 'icon': '🔄', 'url_name': 'producao:reprocessar_lotes', 'required_perms': ['producao.view_reprocessar_lotes']},
            
        ]
    },    
    {
        'name': 'Empresas',
        'icon': '🏢',
        'children': [
            {'name': 'Cadastrar Empresa', 'url_name': 'empresas:cadastrar_empresa', 'required_perms': ['empresas.add_empresa']},
            {'name': 'Lista de Empresas', 'url_name': 'empresas:lista_empresas', 'required_perms': ['empresas.view_empresa']},
            {'name': 'Categorias', 'url_name': 'empresas:lista_categorias', 'required_perms': ['empresas.view_categoriaempresa']},
        ]
    },
    {
        'name': 'Produtos',
        'icon': '📦',
        'children': [
            {'name': 'Cadastro Produtos', 'url_name': 'produto:cadastrar_produto', 'required_perms': ['produto.add_produto']},
            {'name': 'Listar Produtos', 'url_name': 'produto:lista_produtos', 'required_perms': ['produto.view_produto']},
            {'name': 'Categorias de Produto', 'url_name': 'produto:lista_categorias', 'required_perms': ['produto.view_categoriaproduto']},
            {'name': 'Unidades de Medida', 'url_name': 'produto:lista_unidades', 'required_perms': ['produto.view_unidademedida']},
            {'name': 'NCM', 'url_name': 'produto:manutencao_ncm', 'required_perms': ['produto.view_ncm']},
        ]
    },
    {
        'name': 'Produção',
        'icon': '🐟',
        'children': [
            {'name': 'Gerenciar Tanques', 'url_name': 'producao:gerenciar_tanques', 'required_perms': ['producao.view_tanque']},
            {'name': 'Lista de Tanques', 'url_name': 'producao:lista_tanques', 'required_perms': ['producao.view_tanque']},
            {'name': 'Importar Curva', 'url_name': 'producao:importar_curva', 'required_perms': ['producao.add_curva']},
            {'name': 'Cadastrar Curva', 'url_name': 'producao:cadastrar_curva', 'required_perms': ['producao.add_curva']},
            {'name': 'Lista de Curvas', 'url_name': 'producao:lista_curvas', 'required_perms': ['producao.view_curva']},
            {'name': 'Gerenciar Curvas', 'url_name': 'producao:gerenciar_curvas', 'required_perms': ['producao.view_curvacrescimento']},
            {'name': 'Cadastrar Lote', 'url_name': 'producao:cadastrar_lote', 'required_perms': ['producao.add_lote']},
            {'name': 'Lista de Lotes', 'url_name': 'producao:lista_lotes', 'required_perms': ['producao.view_lote']},
            {'name': 'Povoamento de Lotes', 'url_name': 'producao:povoamento_lotes', 'required_perms': ['producao.add_lote']},
            {'name': 'Arraçoamento Diário', 'url_name': 'producao:arracoamento_diario', 'required_perms': ['producao.view_arracoamentosugerido']},
            {'name': 'Gerenciar Eventos', 'url_name': 'producao:gerenciar_eventos', 'required_perms': ['producao.add_eventomanejo']},
            {'name': 'Lista de Eventos', 'url_name': 'producao:lista_eventos', 'required_perms': ['producao.view_eventomanejo']},
            
            {'name': 'Unidades', 'url_name': 'producao:lista_unidades', 'required_perms': ['producao.view_unidade']},
            {'name': 'Malhas', 'url_name': 'producao:lista_malhas', 'required_perms': ['producao.view_malha']},
            {'name': 'Tipos de Tela', 'url_name': 'producao:lista_tipotelas', 'required_perms': ['producao.view_tipotela']},
            {'name': 'Linhas de Produção', 'url_name': 'producao:lista_linhasproducao', 'required_perms': ['producao.view_linhaproducao']},
            {'name': 'Fases de Produção', 'url_name': 'producao:lista_fasesproducao', 'required_perms': ['producao.view_faseproducao']},
            {'name': 'Status de Tanque', 'url_name': 'producao:lista_statustanque', 'required_perms': ['producao.view_statustanque']},
            {'name': 'Tipos de Tanque', 'url_name': 'producao:lista_tipostanque', 'required_perms': ['producao.view_tipotanque']},
            {'name': 'Tipos de Evento', 'url_name': 'producao:lista_tiposevento', 'required_perms': ['producao.view_tipoevento']},
            ]
    },
    {
        'name': 'Comercial',
        'icon': '<i class="bi bi-briefcase"></i>',
        'children': [
            {'name': 'Condicao de Pagamento', 'icon': '<i class="bi bi-cash-coin"></i>', 'url_name': 'comercial:condicao_pagamento_list', 'required_perms': ['comercial.view_condicaopagamento']},
        ]
    },
    {
        'name': 'Nota Fiscal',
        'icon': '📄',
        'children': [
            {'name': 'Criar NF-e (Saída)', 'icon': '➕', 'url_name': 'nota_fiscal:criar_nfe_saida', 'required_perms': ['nota_fiscal.add_notafiscal']},
            {'name': 'Importar XML (Entrada)', 'icon': '📥', 'url_name': 'nota_fiscal:importar_xml', 'required_perms': ['nota_fiscal.add_notafiscal']},
            {'name': 'Lançar Nota Manual (Entrada)', 'icon': '✍️', 'url_name': 'nota_fiscal:lancar_nota_manual', 'required_perms': ['nota_fiscal.add_notafiscal']},
            {'name': 'Emitir NF-e', 'icon': '🚀', 'url_name': 'nota_fiscal:emitir_nfe_list', 'required_perms': ['integracao_nfe.can_emit_nfe']},
            {'name': 'Entradas de Nota', 'url_name': 'nota_fiscal:entradas_nota', 'required_perms': ['nota_fiscal.view_notafiscal']},
        ]
    },
    {
        'name': 'Fiscal',
        'icon': '🧾',
        'children': [
            {'name': 'CFOPs', 'url_name': 'fiscal:cfop_list', 'required_perms': ['fiscal.view_cfop']},
            {'name': 'Naturezas de Operação', 'url_name': 'fiscal:natureza_operacao_list', 'required_perms': ['fiscal.view_naturezaoperacao']},
            {'name': 'Classificacao Fiscal', 'url_name': 'produto:manutencao_ncm', 'required_perms': ['produto.view_ncm']},
            {'name': 'Importar Dados Fiscais', 'url_name': 'fiscal:import_fiscal_data', 'required_perms': ['fiscal.add_cfop']},
            {'name': 'Regras ICMS (NCM)', 'url_name': 'fiscal_regras:regra_icms_list', 'required_perms': ['fiscal_regras.view_regraaliquotaicms']},
            {
                'name': 'Configurações Fiscais',
                'icon': '⚙️',
                'children': [
                    {'name': 'Regras Tributárias (Futuro)', 'url_name': '#', 'required_perms': ['fiscal.view_future_feature']},
                    {'name': 'Status NF-e (Futuro)', 'url_name': '#', 'required_perms': ['fiscal.view_future_feature']},
                ]
            },
        ]
    },
    {
        'name': 'Relatórios',
        'icon': '📊',
        'children': [
            {'name': 'Notas de Entrada', 'url_name': 'relatorios:notas_entradas', 'required_perms': ['relatorios.view_notafiscalrelatorio']},
            {'name': 'Impressão de Relatórios', 'url_name': 'relatorios:impressao_relatorios', 'required_perms': ['relatorios.view_notafiscalrelatorio']},
        ]
    },
]

