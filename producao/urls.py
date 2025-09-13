from django.urls import path
from . import views, views_arracoamento
from .models import LinhaProducao, FaseProducao, StatusTanque, TipoTanque, Tanque, CurvaCrescimento, Lote, EventoManejo

app_name = 'producao'

urlpatterns = [
    # Tanques
    path('tanques/', views.ListaTanquesView.as_view(), name='lista_tanques'),
    path('tanques/cadastrar/', views.CadastrarTanqueView.as_view(), name='cadastrar_tanque'),
    path('tanques/<int:pk>/editar/', views.EditarTanqueView.as_view(), name='editar_tanque'),
    path('tanques/excluir-multiplos/', views.ExcluirTanquesMultiplosView.as_view(), name='excluir_tanques_multiplos'),
    path('tanques/importar/', views.importar_tanques_view, name='importar_tanques'),
    path('tanques/download-template/', views.download_template_tanque_view, name='download_template_tanque'),

    # Entidades de Suporte
    path('unidades/', views.UnidadeListView.as_view(), name='lista_unidades'),
    path('unidades/cadastrar/', views.UnidadeCreateView.as_view(), name='cadastrar_unidade'),
    path('unidades/<int:pk>/editar/', views.UnidadeUpdateView.as_view(), name='editar_unidade'),
    path('malhas/', views.MalhaListView.as_view(), name='lista_malhas'),
    path('malhas/cadastrar/', views.MalhaCreateView.as_view(), name='cadastrar_malha'),
    path('malhas/<int:pk>/editar/', views.MalhaUpdateView.as_view(), name='editar_malha'),
    path('tipos-tela/', views.TipoTelaListView.as_view(), name='lista_tipotelas'),
    path('tipos-tela/cadastrar/', views.TipoTelaCreateView.as_view(), name='cadastrar_tipotela'),
    path('tipos-tela/<int:pk>/editar/', views.TipoTelaUpdateView.as_view(), name='editar_tipotela'),

    # Linhas de Produção
    path('linhas-producao/', views.LinhaProducaoListView.as_view(), name='lista_linhasproducao'),
    path('linhas-producao/cadastrar/', views.LinhaProducaoCreateView.as_view(), name='criar_linhaproducao'),
    path('linhas-producao/<int:pk>/editar/', views.LinhaProducaoUpdateView.as_view(), name='editar_linhaproducao'),
    path('linhas-producao/excluir-multiplos/', views.BulkDeleteView.as_view(model=LinhaProducao, success_url_name='producao:lista_linhasproducao'), name='excluir_linhaproducao_multiplo'),

    # Fases de Produção
    path('fases-producao/', views.FaseProducaoListView.as_view(), name='lista_fasesproducao'),
    path('fases-producao/cadastrar/', views.FaseProducaoCreateView.as_view(), name='criar_faseproducao'),
    path('fases-producao/<int:pk>/editar/', views.FaseProducaoUpdateView.as_view(), name='editar_faseproducao'),
    path('fases-producao/excluir-multiplos/', views.BulkDeleteView.as_view(model=FaseProducao, success_url_name='producao:lista_fasesproducao'), name='excluir_faseproducao_multiplo'),

    # Status de Tanque
    path('status-tanque/', views.StatusTanqueListView.as_view(), name='lista_statustanque'),
    path('status-tanque/cadastrar/', views.StatusTanqueCreateView.as_view(), name='criar_statustanque'),
    path('status-tanque/<int:pk>/editar/', views.StatusTanqueUpdateView.as_view(), name='editar_statustanque'),
    path('status-tanque/excluir-multiplos/', views.BulkDeleteView.as_view(model=StatusTanque, success_url_name='producao:lista_statustanque'), name='excluir_statustanque_multiplo'),

    # Tipos de Tanque
    path('tipos-tanque/', views.TipoTanqueListView.as_view(), name='lista_tipostanque'),
    path('tipos-tanque/cadastrar/', views.TipoTanqueCreateView.as_view(), name='criar_tipotanque'),
    path('tipos-tanque/<int:pk>/editar/', views.TipoTanqueUpdateView.as_view(), name='editar_tipotanque'),
    path('tipos-tanque/excluir-multiplos/', views.BulkDeleteView.as_view(model=TipoTanque, success_url_name='producao:lista_tipostanque'), name='excluir_tipotanque_multiplo'),

    

    # Curvas de Crescimento
    path('curvas/', views.ListaCurvasView.as_view(), name='lista_curvas'),
    path('curvas/cadastrar/', views.CadastrarCurvaView.as_view(), name='cadastrar_curva'),
    path('curvas/<int:pk>/editar/', views.EditarCurvaView.as_view(), name='editar_curva'),
    path('curvas/excluir-multiplas/', views.ExcluirCurvasMultiplasView.as_view(), name='excluir_curvas_multiplas'),
    path('curvas/importar/', views.importar_curva_view, name='importar_curva'),
    path('curvas/download-template/', views.download_template_curva_view, name='download_template_curva'),
    path('curvas/<int:pk>/detalhe/', views.DetalheCurvaView.as_view(), name='detalhe_curva'),

    # Gerenciador de Curvas Interativo
    path('gerenciar-curvas/', views.gerenciar_curvas, name='gerenciar_curvas'),

    # --- API JSON para o Gerenciador de Curvas ---
    path('api/curva/', views.curva_create_view, name='api_curva_create'),
    path('api/curva/<int:curva_id>/', views.curva_update_view, name='api_curva_update'),
    path('api/curva/<int:curva_id>/detalhes/', views.curva_com_detalhes_view, name='api_curva_com_detalhes'),
    path('api/curva/<int:curva_id>/detalhes/criar/', views.detalhe_create_view, name='api_detalhe_create'),
    path('api/curva/<int:curva_id>/detalhes/<int:detalhe_id>/', views.detalhe_view, name='api_detalhe_get'),
    path('api/curva/<int:curva_id>/detalhes/<int:detalhe_id>/atualizar/', views.detalhe_update_view, name='api_detalhe_update'),

    # Gerenciador de Tanques Interativo
    path('gerenciar-tanques/', views.gerenciar_tanques_view, name='gerenciar_tanques'),

    # --- API JSON para o Gerenciador de Tanques ---
    path('api/tanques/<int:pk>/', views.tanque_detail, name='api_tanque_detail'),
    path('api/tanques/<int:pk>/atualizar/', views.tanque_update, name='api_tanque_update'),
    path('api/tanques/', views.tanque_create, name='api_tanque_create'),

    # Lotes
    path('lotes/', views.ListaLotesView.as_view(), name='lista_lotes'),
    path('lotes/cadastrar/', views.CadastrarLoteView.as_view(), name='cadastrar_lote'),
    path('lotes/<int:pk>/editar/', views.EditarLoteView.as_view(), name='editar_lote'),
    path('lotes/excluir-multiplos/', views.ExcluirLotesMultiplosView.as_view(), name='excluir_lotes_multiplos'),

    # Povoamento de Lotes
    path('povoamento/', views.povoamento_lotes_view, name='povoamento_lotes'),
    path('api/povoamento/historico/', views.historico_povoamento_view, name='povoamento_historico_api'),
    path('api/tanque/<int:tanque_id>/lote-ativo/', views.get_active_lote_for_tanque_api, name='api_get_lote_ativo_por_tanque'),

    # Eventos de Manejo
    path('eventos/', views.ListaEventosView.as_view(), name='lista_eventos'),
    path('eventos/registrar/', views.RegistrarEventoView.as_view(), name='registrar_evento'),
    path('eventos/<int:pk>/editar/', views.EditarEventoView.as_view(), name='editar_evento'),
    path('eventos/excluir-multiplos/', views.ExcluirEventosMultiplosView.as_view(), name='excluir_eventos_multiplos'),
    path('eventos/gerenciar/', views.gerenciar_eventos_view, name='gerenciar_eventos'),
    path('api/eventos/mortalidade/', views.api_mortalidade_lotes_ativos, name='api_mortalidade_lotes_ativos'),
    path('api/eventos/mortalidade/processar/', views.processar_mortalidade_api, name='api_processar_mortalidade'),
    path('api/registrar-mortalidade/', views.registrar_mortalidade_api, name='api_registrar_mortalidade'),
    path('api/ultimos-eventos/', views.api_ultimos_eventos, name='api_ultimos_eventos'),

    # Arraçoamento (Sugestões e Aprovações)
    path('arracoamento/diario/', views.arracoamento_diario_view, name='arracoamento_diario'),
    path('api/arracoamento/sugestoes/', views_arracoamento.api_sugestoes_arracoamento, name='api_sugestoes_arracoamento'),
    path('api/arracoamento/aprovar/', views_arracoamento.api_aprovar_arracoamento, name='api_aprovar_arracoamento'),
    path('api/linhas-producao/', views.api_linhas_producao_list, name='api_linhas_producao_list'),
    path('api/arracoamento/realizado/<int:pk>/delete/', views_arracoamento.api_delete_arracoamento_realizado, name='api_delete_arracoamento_realizado'),
    path('api/arracoamento/realizado/bulk-delete/', views_arracoamento.api_bulk_delete_arracoamento_realizado, name='api_bulk_delete_arracoamento_realizado'),
    path('api/arracoamento/realizado/<int:pk>/', views_arracoamento.api_get_arracoamento_realizado, name='api_get_arracoamento_realizado'), # GET for detail
    path('api/arracoamento/realizado/<int:pk>/update/', views_arracoamento.api_update_arracoamento_realizado, name='api_update_arracoamento_realizado'), # POST for update
]
