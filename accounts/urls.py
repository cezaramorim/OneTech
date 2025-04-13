from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [

    # === AUTENTICAÇÃO ===
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('logout-auto/', views.logout_automatico_view, name='logout_automatico'),

    # === PERFIL DO USUÁRIO ===
    path('edit-profile/', views.edit_profile_view, name='edit_profile'),

    # === USUÁRIOS ===
    path('usuarios/', views.lista_usuarios, name='lista_usuarios'),    
    path('usuarios/<int:usuario_id>/editar/', views.editar_usuario, name='editar_usuario'),
    path('usuarios/excluir-multiplos/', views.excluir_usuario_multiplo, name='excluir_usuario_multiplo'),

    # === PERMISSÕES GERAIS ===
    path('permissoes/', views.selecionar_usuario_permissoes_view, name='selecionar_usuario_permissoes'),
    path('permissoes/editar/<int:usuario_id>/', views.editar_permissoes_view, name='editar_permissoes'),
    path('permissoes/gerenciar/', views.gerenciar_permissoes_geral, name='gerenciar_permissoes_geral'),

    # === PERMISSÕES POR GRUPO ===
    path('permissoes/por-grupo/', views.gerenciar_permissoes_grupo_view_selector, name='selecionar_grupo_permissoes'),
    path('grupos/<int:grupo_id>/permissoes/', views.gerenciar_permissoes_grupo_view, name='gerenciar_permissoes_grupo'),
    path('grupos/<int:grupo_id>/ver-permissoes/', views.visualizar_permissoes_grupo_view, name='visualizar_permissoes_grupo'),
     path('grupos/selecionar/', views.seletor_grupo_permissoes, name='gerenciar_permissoes_grupo_selector'),

    # === GRUPOS ===
    path('grupos/', views.lista_grupos, name='lista_grupos'),
    path('grupos/novo/', views.cadastrar_grupo, name='cadastrar_grupo'),
    path('grupos/<int:grupo_id>/editar/', views.editar_grupo, name='editar_grupo'),
    path('grupos/excluir/<int:grupo_id>/', views.confirmar_exclusao_grupo, name='confirmar_exclusao_grupo'),
    path('grupos/excluir/<int:grupo_id>/confirmar/', views.excluir_grupo, name='excluir_grupo'),
    path('grupos/excluir/', views.excluir_grupo_multiplo, name='excluir_grupo_multiplo'),
    
]


