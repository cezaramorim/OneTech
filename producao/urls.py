from django.urls import path
from . import views

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
    path('linhas-producao/excluir-multiplos/', views.BulkDeleteView.as_view(model=views.LinhaProducao), name='excluir_linhaproducao_multiplo'),

    # Fases de Produção
    path('fases-producao/', views.FaseProducaoListView.as_view(), name='lista_fasesproducao'),
    path('fases-producao/cadastrar/', views.FaseProducaoCreateView.as_view(), name='criar_faseproducao'),
    path('fases-producao/<int:pk>/editar/', views.FaseProducaoUpdateView.as_view(), name='editar_faseproducao'),
    path('fases-producao/excluir-multiplos/', views.BulkDeleteView.as_view(model=views.FaseProducao), name='excluir_faseproducao_multiplo'),

    # Status de Tanque
    path('status-tanque/', views.StatusTanqueListView.as_view(), name='lista_statustanque'),
    path('status-tanque/cadastrar/', views.StatusTanqueCreateView.as_view(), name='criar_statustanque'),
    path('status-tanque/<int:pk>/editar/', views.StatusTanqueUpdateView.as_view(), name='editar_statustanque'),
    path('status-tanque/excluir-multiplos/', views.BulkDeleteView.as_view(model=views.StatusTanque), name='excluir_statustanque_multiplo'),

    # Tipos de Tanque
    path('tipos-tanque/', views.TipoTanqueListView.as_view(), name='lista_tipostanque'),
    path('tipos-tanque/cadastrar/', views.TipoTanqueCreateView.as_view(), name='criar_tipotanque'),
    path('tipos-tanque/<int:pk>/editar/', views.TipoTanqueUpdateView.as_view(), name='editar_tipotanque'),
    path('tipos-tanque/excluir-multiplos/', views.BulkDeleteView.as_view(model=views.TipoTanque), name='excluir_tipotanque_multiplo'),

    

    # Curvas de Crescimento
    path('curvas/', views.ListaCurvasView.as_view(), name='lista_curvas'),
    path('curvas/cadastrar/', views.CadastrarCurvaView.as_view(), name='cadastrar_curva'),
    path('curvas/<int:pk>/editar/', views.EditarCurvaView.as_view(), name='editar_curva'),
    path('curvas/excluir-multiplas/', views.ExcluirCurvasMultiplasView.as_view(), name='excluir_curvas_multiplas'),
    path('curvas/importar/', views.importar_curva_view, name='importar_curva'),
    path('curvas/download-template/', views.download_template_curva_view, name='download_template_curva'),
    path('curvas/<int:pk>/detalhe/', views.DetalheCurvaView.as_view(), name='detalhe_curva'),

    # Lotes
    path('lotes/', views.ListaLotesView.as_view(), name='lista_lotes'),
    path('lotes/cadastrar/', views.CadastrarLoteView.as_view(), name='cadastrar_lote'),
    path('lotes/<int:pk>/editar/', views.EditarLoteView.as_view(), name='editar_lote'),
    path('lotes/excluir-multiplos/', views.ExcluirLotesMultiplosView.as_view(), name='excluir_lotes_multiplos'),

    # Eventos de Manejo
    path('eventos/', views.ListaEventosView.as_view(), name='lista_eventos'),
    path('eventos/registrar/', views.RegistrarEventoView.as_view(), name='registrar_evento'),
    path('eventos/<int:pk>/editar/', views.EditarEventoView.as_view(), name='editar_evento'),
    path('eventos/excluir-multiplos/', views.ExcluirEventosMultiplosView.as_view(), name='excluir_eventos_multiplos'),

    # Alimentação Diária
    path('alimentacao/', views.ListaAlimentacaoView.as_view(), name='lista_alimentacao'),
    path('alimentacao/registrar/', views.RegistrarAlimentacaoView.as_view(), name='registrar_alimentacao'),
    path('alimentacao/<int:pk>/editar/', views.EditarAlimentacaoView.as_view(), name='editar_alimentacao'),
    path('alimentacao/excluir-multipla/', views.ExcluirAlimentacaoMultiplaView.as_view(), name='excluir_alimentacao_multipla'),

    # API para Edição Interativa de Detalhes da Curva
    path('api/curvas/detalhe/atualizar/', views.AtualizarDetalheCurvaAPIView.as_view(), name='api_atualizar_detalhe_curva'),
]
