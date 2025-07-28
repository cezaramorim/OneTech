from django.urls import path
from . import views

app_name = 'producao'

urlpatterns = [
    # Tanques
    path('tanques/', views.ListaTanquesView.as_view(), name='lista_tanques'),
    path('tanques/cadastrar/', views.CadastrarTanqueView.as_view(), name='cadastrar_tanque'),
    path('tanques/<int:pk>/editar/', views.EditarTanqueView.as_view(), name='editar_tanque'),
    path('tanques/excluir-multiplos/', views.ExcluirTanquesMultiplosView.as_view(), name='excluir_tanques_multiplos'),

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
