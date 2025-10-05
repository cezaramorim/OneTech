# producao/signals.py
from django.db.models.signals import post_save, post_delete, pre_delete
from django.dispatch import receiver
from .models import EventoManejo, Lote, LoteDiario
from .utils import _apurar_quantidade_real_no_dia, reprojetar_ciclo_de_vida
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
    Dispara o recálculo da quantidade real de um LoteDiario sempre que um
    EventoManejo é criado, alterado ou excluído.
    """
    lote = instance.lote
    data_evento = instance.data_evento

    # Garante que o LoteDiario para a data do evento exista.
    lote_diario, created = LoteDiario.objects.get_or_create(
        lote=lote,
        data_evento=data_evento
    )

    # Define a quantidade inicial correta, baseada no dia anterior ou no povoamento do lote.
    dia_anterior = data_evento - timedelta(days=1)
    lote_diario_anterior = LoteDiario.objects.filter(lote=lote, data_evento=dia_anterior).first()

    if lote_diario_anterior and lote_diario_anterior.quantidade_real is not None:
        lote_diario.quantidade_inicial = lote_diario_anterior.quantidade_real
    else:
        lote_diario.quantidade_inicial = lote.quantidade_inicial

    # Apura e salva a nova quantidade real.
    lote_diario.quantidade_real = _apurar_quantidade_real_no_dia(lote_diario)
    lote_diario.save(update_fields=['quantidade_inicial', 'quantidade_real'])

    # Reprojeta o ciclo de vida a partir do dia seguinte ao evento.
    reprojetar_ciclo_de_vida(lote, data_evento + timedelta(days=1))