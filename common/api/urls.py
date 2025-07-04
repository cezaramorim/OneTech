# common/api/urls.py
from rest_framework.routers import DefaultRouter
from .nota_fiscal import NotaFiscalViewSet
from .fiscal import CfopViewSet, NaturezaOperacaoViewSet

router = DefaultRouter()
router.register(r'notas-entradas', NotaFiscalViewSet, basename='notas-entradas')
router.register(r'fiscal/cfops', CfopViewSet, basename='fiscal-cfops')
router.register(r'fiscal/naturezas-operacao', NaturezaOperacaoViewSet, basename='fiscal-naturezas-operacao')

urlpatterns = router.urls
