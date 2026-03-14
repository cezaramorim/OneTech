# control/urls.py
from django.urls import path

from . import views

app_name = 'control'

urlpatterns = [
    path('ping/', views.ping_view, name='ping'),
    path('seguranca/', views.central_seguranca_view, name='central_seguranca'),
    path('seguranca/eventos/exportar-csv/', views.security_export_events_csv_view, name='security_export_events_csv'),
    path('seguranca/auditoria/', views.security_run_audit_view, name='security_run_audit'),
    path('seguranca/auditoria-matriz/', views.security_run_matrix_audit_view, name='security_run_matrix_audit'),
    path('seguranca/auditoria-dependencias/', views.security_run_dependency_audit_view, name='security_run_dependency_audit'),
    path('seguranca/exportar-consolidado/', views.security_export_consolidated_view, name='security_export_consolidated'),
    path('seguranca/siem-eventos/', views.security_siem_events_view, name='security_siem_events'),
    path('seguranca/encerrar-sessoes/', views.security_force_logout_user_view, name='security_force_logout_user'),
    path('seguranca/bloquear-usuario/', views.security_toggle_user_lock_view, name='security_toggle_user_lock'),
    path('seguranca/quarentena-tenant/', views.security_toggle_tenant_quarantine_view, name='security_toggle_tenant_quarantine'),

    path('tenants/', views.tenant_list_view, name='tenant_list'),
    path('tenants/new/', views.tenant_create_view, name='tenant_create'),
    path('tenants/edit/<int:pk>/', views.tenant_edit_view, name='tenant_edit'),
    path('tenants/excluir-multiplos/', views.tenant_delete_multiplo_view, name='tenant_delete_multiplo'),

    # URLs para gerenciamento de usuarios de um tenant especifico
    path('tenants/<int:tenant_id>/users/', views.tenant_user_list_view, name='tenant_user_list'),
    path('tenants/<int:tenant_id>/users/new/', views.tenant_user_create_view, name='tenant_user_create'),
    path('tenants/<int:tenant_id>/users/edit/<int:user_id>/', views.tenant_user_edit_view, name='tenant_user_edit'),
    path('tenants/<int:tenant_id>/users/toggle-active/<int:user_id>/', views.tenant_user_toggle_active_view, name='tenant_user_toggle_active'),

    # URLs para gerenciamento de Emitentes (Matriz/Filiais)
    path('emitentes/', views.lista_emitentes, name='lista_emitentes'),
    path('emitentes/novo/', views.criar_emitente, name='criar_emitente'),
    path('emitentes/<int:pk>/editar/', views.editar_emitente, name='editar_emitente'),
    path('emitentes/<int:pk>/excluir/', views.excluir_emitente, name='excluir_emitente'),
    path('emitentes/excluir-multiplos/', views.excluir_emitentes_multiplo, name='excluir_emitentes_multiplo'),

    path('migracoes/', views.central_migracoes_view, name='central_migracoes'),
]

