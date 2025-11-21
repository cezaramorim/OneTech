# control/urls.py
from django.urls import path
from . import views

app_name = 'control'

urlpatterns = [
    path('ping/', views.ping_view, name='ping'),
    path('tenants/', views.tenant_list_view, name='tenant_list'),
    path('tenants/new/', views.tenant_create_view, name='tenant_create'),
    path('tenants/edit/<int:pk>/', views.tenant_edit_view, name='tenant_edit'),
    
    # URLs para gerenciamento de usuários de um tenant específico
    path('tenants/<int:tenant_id>/users/', views.tenant_user_list_view, name='tenant_user_list'),
    path('tenants/<int:tenant_id>/users/new/', views.tenant_user_create_view, name='tenant_user_create'),
    path('tenants/<int:tenant_id>/users/edit/<int:user_id>/', views.tenant_user_edit_view, name='tenant_user_edit'),
    path('tenants/<int:tenant_id>/users/toggle-active/<int:user_id>/', views.tenant_user_toggle_active_view, name='tenant_user_toggle_active'),
]
