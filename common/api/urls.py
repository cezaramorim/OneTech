# common/api/urls.py
from rest_framework.routers import DefaultRouter
from .nota_fiscal import NotaFiscalViewSet
from .fiscal import CfopViewSet, NaturezaOperacaoViewSet
from .item_nota_fiscal import ItemNotaFiscalViewSet

router = DefaultRouter()
router.register(r'notas-entradas', NotaFiscalViewSet, basename='notas-entradas')
router.register(r'fiscal/cfops', CfopViewSet, basename='fiscal-cfops')
router.register(r'fiscal/naturezas-operacao', NaturezaOperacaoViewSet, basename='fiscal-naturezas-operacao')
router.register(r'nota-fiscal/itens', ItemNotaFiscalViewSet, basename='nota-fiscal-itens')

urlpatterns = router.urls
