from rest_framework import serializers
from .models import Tanque

class TanqueSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tanque
        fields = (
            "id","nome","data_criacao","largura","profundidade","comprimento",
            "metro_cubico","metro_quadrado","ha",
            "unidade","fase","tipo_tanque","linha_producao","sequencia",
            "malha","status_tanque","tag_tanque","ativo",
            "unidade_id","fase_id","tipo_tanque_id","linha_producao_id","malha_id","status_tanque_id",
        )
        read_only_fields = ("id","data_criacao")

