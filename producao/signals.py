# producao/signals.py
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from .models import Lote

@receiver(pre_delete, sender=Lote)
def on_lote_delete(sender, instance, **kwargs):
    """
    Antes de um Lote ser deletado, verifica se o tanque associado
    deve ter seu status alterado para 'Livre'.
    """
    if instance.tanque_atual:
        # A lógica de verificação e atualização foi centralizada no modelo Tanque
        # para ser reutilizada. O parâmetro 'lote_sendo_deletado' é crucial
        # para que a verificação exclua o lote que está prestes a ser removido.
        instance.tanque_atual.verificar_e_liberar_status(lote_sendo_deletado=instance)
