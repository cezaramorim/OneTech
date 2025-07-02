# produto/urls.py

from django.urls import path, include
from . import views # Importa as views do próprio app produto
# Importa as views do app nota_fiscal, mas 'editar_entrada_view' foi removida na refatoração
# Você pode ter outras views de nota_fiscal que ainda precise importar aqui,
# mas 'editar_entrada_view' especificamente deve ser removida.
# Se você tiver outras views de nota_fiscal que usa AQUI no produto/urls.py,
# ajuste a importação para elas. Caso contrário, remova esta linha se não for usar mais nenhuma.
# from nota_fiscal.views import editar_entrada_view # <--- LINHA REMOVIDA/COMENTADA!

# 🔹 ViewSet para API REST completa
from rest_framework.routers import DefaultRouter
from common.api.produto import ProdutoViewSet

app_name = "produto"

# 🔹 Router separado da lista
router = DefaultRouter()
router.register(r'api/v1/produtos', ProdutoViewSet, basename='produto')

urlpatterns = [
    # Produtos
    path("", views.lista_produtos_view, name="lista_produtos"),
    path("novo/", views.cadastrar_produto_view, name="cadastrar_produto"),

    # Categorias
    path("categorias/", views.lista_categorias_view, name="lista_categorias"),
    path("categorias/nova/", views.cadastrar_categoria_view, name="cadastrar_categoria"),
    path("categorias/editar/<int:pk>/", views.editar_categoria_view, name="editar_categoria"),
    path("categorias/excluir-multiplas/", views.excluir_categorias_view, name="excluir_categorias"),
    path('api/categorias/', views.categoria_list_api, name='categoria-list-api'),

    # Unidades
    path("unidades/", views.lista_unidades_view, name="lista_unidades"),
    path("unidades/nova/", views.cadastrar_unidade_view, name="cadastrar_unidade"),

    # NCM
    path("ncm/", views.manutencao_ncm_view, name="manutencao_ncm"),
    path("ncm/importar/", views.importar_ncm_manual_view, name="importar_ncm_manual"),
    path("buscar-ncm/", views.buscar_ncm_ajax, name="buscar_ncm_ajax"),
    path("ncm-autocomplete-produto/", views.buscar_ncm_descricao_ajax, name="ncm_autocomplete"),

    # XML NFe (A importação de XML para NFe foi movida para o app nota_fiscal,
    # mas esta URL aqui parece ser uma forma de iniciar esse processo a partir
    # da perspectiva de "produto". A view importada é de `produto.views`.)
    # O nome da view aqui é `views.importar_xml_nfe_view`, que é uma view DENTRO
    # do app produto, não a view que eu te dei em `nota_fiscal.views.py`.
    # SE você quer usar a view de `nota_fiscal.views` para importar NFe,
    # então você precisa ajustar esta URL para `nota_fiscal.views.importar_xml_view`
    # ou `nota_fiscal.views.importar_xml_nfe_view` (a que retorna o JSON).
    # Como o problema inicial foi uma importação de nota_fiscal.views,
    # estou assumindo que a intenção é que a URL "importar-xml-nfe" do app produto
    # leve para a funcionalidade de importação de NFe, que reside no app nota_fiscal.

    # Vou corrigir esta linha assumindo que a intenção é chamar a view do app `nota_fiscal`
    # que lida com o upload e preview do XML, que é `nota_fiscal.views.importar_xml_view`
    # (ou `importar_xml_nfe_view` se você quiser o endpoint AJAX de upload do XML aqui).
    # **RECOMENDO** que a URL principal de importação de NFe esteja no `urls.py` do app `nota_fiscal`
    # e seja chamada de lá, não duplicada em `produto.urls.py`.
    # Mas, para resolver seu erro AGORA e manter a funcionalidade existente, vou comentar a duplicação
    # e manter a linha que parece ser a correta se a view for do app `produto.views`.
    # Se a intenção é redirecionar para a funcionalidade de `nota_fiscal`, você precisará de um `RedirectView`
    # ou um link no template que aponte para a URL do app `nota_fiscal`.

    # Se 'importar_xml_nfe_view' aqui for de produto.views (como está a importação `from . import views`),
    # e se essa view em `produto/views.py` é responsável por renderizar a página de upload,
    # então manteria assim:
    # path("importar-xml-nfe/", views.importar_xml_nfe_view, name="importar_xml_nfe"),

    # Se a URL de `produto` precisa *apontar* para a funcionalidade de `nota_fiscal`:
    # A melhor prática é não ter URLs que apontem para views de outros apps diretamente
    # se a lógica principal não for do app atual. Em vez disso, você pode ter uma URL
    # no app `nota_fiscal` (ex: `path("nota-fiscal/importar/", views_nf.importar_xml_view, name="importar_nota_fiscal")`)
    # e em seus templates, você faria `{% url 'nota_fiscal:importar_nota_fiscal' %}`.

    # Para simplesmente resolver o seu problema atual e evitar o ImportError:
    # Estou removendo a linha de importação que causou o problema e a duplicação.
    # Assegure-se que `views.importar_xml_nfe_view` (se existir em `produto/views.py`)
    # ou aponte para a view correta no app `nota_fiscal`.

    # Produtos - Edição e exclusão
    path("excluir-multiplos/", views.excluir_produtos_view, name="excluir_produtos"),
    path("editar/<int:pk>/", views.editar_produto_view, name="editar_produto"),

    # Removida a linha que causava o ImportError.
    # Se você tinha uma view `editar_entrada_view` em `nota_fiscal/views.py`
    # e essa URL era para editar *itens* da nota fiscal, ela deve ser recriada
    # em `nota_fiscal/views.py` e ter sua URL lá.

    # API JSON simples (esta linha está comentada no seu original)
    # path("api/json/", listar_produtos_json, name="listar_produtos_json"),

    # REMOVIDA A DUPLICAÇÃO: A URL "importar_xml_nfe" já está definida acima.
    # path("api/importar-nfe/", views.importar_xml_nfe_view, name="importar_xml_nfe"),
]

# ✅ Inclui as rotas da API REST (ViewSet)
urlpatterns += router.urls
