from rest_framework import serializers

from empresas.models import EmpresaAvancada


# Serializer completo para uso administrativo do cadastro de empresas.
class EmpresaSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmpresaAvancada
        fields = '__all__'


# Alias de compatibilidade com o nome tecnico anterior.
EmpresaAvancadaCompletaSerializer = EmpresaSerializer
