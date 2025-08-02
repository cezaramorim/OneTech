from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

app_name = 'accounts'

urlpatterns = [

    # === AUTENTICAÇÃO ===
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('logout-auto/', views.logout_automatico_view, name='logout_automatico'),
    path('get-navbar/', views.get_navbar_content, name='get_navbar_content'),

    # === RECUPERAÇÃO DE SENHA ===
    path('password_reset/', views.password_reset_request_view, name='password_reset'),  # View customizada
    path('password_reset/done/', views.CustomPasswordResetDoneView.as_view(template_name='accounts/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', views.CustomPasswordResetConfirmView.as_view(template_name='accounts/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', views.CustomPasswordResetCompleteView.as_view(template_name='accounts/password_reset_complete.html'), name='password_reset_complete'),


    # === PERFIL DO USUÁRIO ===
    path('edit-profile/', views.edit_profile_view, name='edit_profile'),

    # === USUÁRIOS ===
    path('usuarios/novo/', views.criar_usuario, name='criar_usuario'),
    path('usuarios/', views.lista_usuarios, name='lista_usuarios'),    
    path('usuarios/<int:usuario_id>/editar/', views.editar_usuario, name='editar_usuario'),
    path('usuarios/excluir-multiplos/', views.excluir_usuario_multiplo, name='excluir_usuario_multiplo'),

    # === PERMISSÕES ===
    # URLs refatoradas para clareza e responsabilidade única
    path('usuarios/<int:user_id>/permissoes/', views.gerenciar_permissoes_usuario, name='gerenciar_permissoes_usuario'),
    path('grupos/<int:group_id>/permissoes/', views.gerenciar_permissoes_grupo, name='gerenciar_permissoes_grupo'),

    # === GRUPOS ===
    path('grupos/', views.lista_grupos, name='lista_grupos'),
    path('grupos/novo/', views.cadastrar_grupo, name='cadastrar_grupo'),
    path('grupos/<int:grupo_id>/editar/', views.editar_grupo, name='editar_grupo'),
    path('grupos/excluir/<int:grupo_id>/', views.confirmar_exclusao_grupo, name='confirmar_exclusao_grupo'),
    path('grupos/excluir/<int:grupo_id>/confirmar/', views.excluir_grupo, name='excluir_grupo'),
    path('grupos/excluir/', views.excluir_grupo_multiplo, name='excluir_grupo_multiplo'),
        
]


