from django.urls import path
from . import views

app_name = 'producao'

urlpatterns = [
    path('tanques/', views.lista_tanques_view, name='lista_tanques'),
    path('tanques/cadastrar/', views.cadastrar_tanque_view, name='cadastrar_tanque'),
    path('tanques/<int:pk>/editar/', views.editar_tanque_view, name='editar_tanque'),
    path('tanques/excluir-multiplos/', views.excluir_tanques_multiplos_view, name='excluir_tanques_multiplos'),

    path('curvas/', views.lista_curvas_view, name='lista_curvas'),
    path('curvas/cadastrar/', views.cadastrar_curva_view, name='cadastrar_curva'),
    path('curvas/<int:pk>/editar/', views.editar_curva_view, name='editar_curva'),
    path('curvas/excluir-multiplas/', views.excluir_curvas_multiplas_view, name='excluir_curvas_multiplas'),

    path('lotes/', views.lista_lotes_view, name='lista_lotes'),
    path('lotes/cadastrar/', views.cadastrar_lote_view, name='cadastrar_lote'),
    path('lotes/<int:pk>/editar/', views.editar_lote_view, name='editar_lote'),
    path('lotes/excluir-multiplos/', views.excluir_lotes_multiplos_view, name='excluir_lotes_multiplos'),

    path('eventos/', views.lista_eventos_view, name='lista_eventos'),
    path('eventos/registrar/', views.registrar_evento_view, name='registrar_evento'),
    path('eventos/<int:pk>/editar/', views.editar_evento_view, name='editar_evento'),
    path('eventos/excluir-multiplos/', views.excluir_eventos_multiplos_view, name='excluir_eventos_multiplos'),

    path('alimentacao/', views.lista_alimentacao_view, name='lista_alimentacao'),
    path('alimentacao/registrar/', views.registrar_alimentacao_view, name='registrar_alimentacao'),
    path('alimentacao/<int:pk>/editar/', views.editar_alimentacao_view, name='editar_alimentacao'),
    path('alimentacao/excluir-multipla/', views.excluir_alimentacao_multipla_view, name='excluir_alimentacao_multipla'),
]