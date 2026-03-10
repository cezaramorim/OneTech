from django.urls import path

from . import views

app_name = 'comercial'

urlpatterns = [
    path('condicoes-pagamento/', views.condicao_pagamento_list, name='condicao_pagamento_list'),
    path('condicoes-pagamento/cadastrar/', views.condicao_pagamento_create, name='condicao_pagamento_create'),
    path('condicoes-pagamento/editar/<int:pk>/', views.condicao_pagamento_update, name='condicao_pagamento_update'),
    path('condicoes-pagamento/excluir-selecionados/', views.delete_condicoes_pagamento, name='delete_condicoes_pagamento'),
]
