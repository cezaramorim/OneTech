from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from decimal import Decimal
from .models import Tanque, Lote, CurvaCrescimentoDetalhe, EventoManejo

class TanqueSerializer(serializers.ModelSerializer):
    # Adiciona os campos read-only que vêm das propriedades do modelo
    volume_calculado_m3 = serializers.ReadOnlyField()
    densidade_peixes_m3 = serializers.ReadOnlyField()
    densidade_kg_m3 = serializers.ReadOnlyField()

    class Meta:
        model = Tanque
        fields = (
            "id","nome","data_criacao","largura","profundidade","comprimento",
            "metro_cubico","metro_quadrado","ha",
            "unidade","fase","tipo_tanque","linha_producao","sequencia",
            "malha","status_tanque","tag_tanque","ativo",
            "unidade_id","fase_id","tipo_tanque_id","linha_producao_id","malha_id","status_tanque_id",
            # Novos campos calculados
            "volume_calculado_m3", "densidade_peixes_m3", "densidade_kg_m3",
        )
        read_only_fields = ("id","data_criacao", "volume_calculado_m3", "densidade_peixes_m3", "densidade_kg_m3")

class LoteSerializer(serializers.ModelSerializer):
    biomassa_inicial_kg = serializers.ReadOnlyField()
    biomassa_atual_kg = serializers.ReadOnlyField()

    class Meta:
        model = Lote
        fields = '__all__'

    def validate(self, data):
        """Garante que valores numéricos não sejam negativos."""
        for field_name in ['quantidade_inicial', 'peso_medio_inicial', 'quantidade_atual', 'peso_medio_atual']:
            # Usa .get() para não falhar se o campo não estiver no payload (em um PATCH, por exemplo)
            value = data.get(field_name, self.instance.get(field_name) if self.instance else None)
            if value is not None and value < 0:
                raise ValidationError({field_name: "Este valor não pode ser negativo."})
        return data

class EventoManejoSerializer(serializers.ModelSerializer):
    biomassa_kg = serializers.ReadOnlyField()

    class Meta:
        model = EventoManejo
        fields = '__all__'

    def validate(self, data):
        """Garante que quantidade e peso não sejam negativos."""
        for field_name in ['quantidade', 'peso_medio']:
            value = data.get(field_name, self.instance.get(field_name) if self.instance else None)
            if value is not None and value < 0:
                raise ValidationError({field_name: "Este valor não pode ser negativo."})
        return data

class CurvaCrescimentoDetalheSerializer(serializers.ModelSerializer):
    class Meta:
        model = CurvaCrescimentoDetalhe
        fields = '__all__'

    def validate_arracoamento_biomassa_perc(self, value):
        """Valida se o %BW/dia está em um range aceitável."""
        if value is not None and not (Decimal('0') <= value <= Decimal('20')):
            raise ValidationError("O percentual de arraçoamento deve estar entre 0 e 20%.")
        return value

    def validate(self, data):
        """Valida a sobreposição de faixas de peso e a lógica da faixa."""
        instance = self.instance
        curva = instance.curva if instance else self.context.get('curva')
        
        peso_inicial = data.get('peso_inicial', instance.peso_inicial if instance else None)
        peso_final = data.get('peso_final', instance.peso_final if instance else None)

        if peso_inicial is not None and peso_final is not None:
            if peso_inicial >= peso_final:
                raise ValidationError({'peso_final': "O peso final deve ser maior que o peso inicial."})

            if curva:
                qs = CurvaCrescimentoDetalhe.objects.filter(curva=curva)
                if instance and instance.pk:
                    qs = qs.exclude(pk=instance.pk)
                
                for detalhe in qs:
                    if (peso_inicial < detalhe.peso_final) and (peso_final > detalhe.peso_inicial):
                        raise ValidationError(
                            f"A faixa de peso ({peso_inicial}g - {peso_final}g) sobrepõe uma faixa existente "
                            f"({detalhe.peso_inicial}g - {detalhe.peso_final}g) para esta curva."
                        )
        return data

