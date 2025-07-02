# common/api/urls.py
from rest_framework.routers import DefaultRouter
from .nota_fiscal import NotaFiscalViewSet

router = DefaultRouter()
router.register(r'notas-entradas', NotaFiscalViewSet, basename='notas-entradas')

urlpatterns = router.urls
