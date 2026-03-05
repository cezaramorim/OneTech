# producao/signals.py
from django.db.models.signals import post_save, post_delete, pre_delete
from django.dispatch import receiver
from .models import EventoManejo, Lote, LoteDiario
from .utils import recalcular_lote_diario_real, reprojetar_ciclo_de_vida
from datetime import timedelta

@receiver(pre_delete, sender=Lote)
def on_lote_delete(sender, instance, **kwargs):
    """
    Antes de um Lote ser deletado, verifica se o tanque associado
    deve ter seu status alterado para 'Livre'.
    """
    if instance.tanque_atual:
        instance.tanque_atual.verificar_e_liberar_status(lote_sendo_deletado=instance)

@receiver([post_save, post_delete], sender=EventoManejo)
def recalcular_lote_diario_on_evento_change(sender, instance, **kwargs):
    """
    Dispara o recálculo de um LoteDiario sempre que um
    EventoManejo (como mortalidade) é criado, alterado ou excluído.
    """
    lote = instance.lote
    data_evento = instance.data_evento

    # Garante que o LoteDiario para a data do evento exista.
    lote_diario, created = LoteDiario.objects.get_or_create(
        lote=lote,
        data_evento=data_evento
    )

    # A função recalcular_lote_diario_real agora centraliza toda a lógica de cálculo.
    # Ela busca o dia anterior, calcula mortalidade, quantidade final, biomassa, etc., e salva o objeto.
    recalcular_lote_diario_real(lote_diario, commit=True)

    # Após o recálculo do dia do evento, a projeção para os dias seguintes
    # é refeita para refletir imediatamente as mudanças nos dados reais.
    # A função `reprojetar_ciclo_de_vida` utiliza os dados atualizados do dia anterior
    # (que acabaram de ser recalculados) como ponto de partida.
    reprojetar_ciclo_de_vida(lote, data_evento + timedelta(days=1))
