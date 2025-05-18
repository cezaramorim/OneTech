# common/serializers/empresa.py

from rest_framework import serializers
from empresas.models import EmpresaAvancada

# ✅ Serializer completo para uso administrativo da empresa avançada
class EmpresaAvancadaCompletaSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmpresaAvancada
        fields = '__all__'
        # Inclui todos os campos do model para uso total em APIs administrativas
