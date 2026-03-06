from rest_framework import serializers

from empresas.models import Empresa


# Serializer completo para uso administrativo do cadastro de empresas.
class EmpresaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Empresa
        fields = '__all__'


# Alias de compatibilidade com o nome tecnico anterior.
EmpresaCompletaSerializer = EmpresaSerializer
