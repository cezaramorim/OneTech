# common/menu_config.py

MENU_ITEMS = [
    {
        'name': 'Configurações',
        'icon': '⚙️',
        'children': [
            {'name': 'Novo Usuário', 'icon': '👤', 'url_name': 'accounts:criar_usuario', 'required_perms': ['accounts.add_user']},
            {'name': 'Lista de Usuários', 'icon': '👤', 'url_name': 'accounts:lista_usuarios', 'required_perms': ['accounts.view_user']},
            {'name': 'Novo Grupo', 'icon': '🛡️', 'url_name': 'accounts:cadastrar_grupo', 'required_perms': ['auth.add_group']},
            {'name': 'Lista de Grupos', 'icon': '🛡️', 'url_name': 'accounts:lista_grupos', 'required_perms': ['auth.view_group']},
        ]
    },
    {
        'name': 'Empresas',
        'icon': '🏢',
        'children': [
            {'name': 'Cadastrar Empresa', 'url_name': 'empresas:cadastrar_empresa_avancada', 'required_perms': ['empresas.add_empresaavancada']},
            {'name': 'Lista de Empresas', 'url_name': 'empresas:lista_empresas_avancadas', 'required_perms': ['empresas.view_empresaavancada']},
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
            ]
    },
    {
        'name': 'Nota Fiscal',
        'icon': '📄',
        'children': [
            {'name': 'Importar XML', 'url_name': 'nota_fiscal:importar_xml', 'required_perms': ['nota_fiscal.add_notafiscal']},
            {'name': 'Lançar Nota Manual', 'url_name': 'nota_fiscal:lancar_nota_manual', 'required_perms': ['nota_fiscal.add_notafiscal']},
            {'name': 'Entradas de Nota', 'url_name': 'nota_fiscal:entradas_nota', 'required_perms': ['nota_fiscal.view_notafiscal']},
        ]
    },
    {
        'name': 'Fiscal',
        'icon': '🧾',
        'children': [
            {'name': 'CFOPs', 'url_name': 'fiscal:cfop_list', 'required_perms': ['fiscal.view_cfop']},
            {'name': 'Naturezas de Operação', 'url_name': 'fiscal:natureza_operacao_list', 'required_perms': ['fiscal.view_naturezaoperacao']},
            {'name': 'Importar Dados Fiscais', 'url_name': 'fiscal:import_fiscal_data', 'required_perms': ['fiscal.add_cfop']},
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
            {'name': 'Nota Fiscal', 'url_name': 'relatorios:api_nota_detalhada', 'required_perms': ['relatorios.view_notafiscalrelatorio']},
        ]
    },
]
