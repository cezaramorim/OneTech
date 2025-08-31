from django.contrib import messages

def _get_model_verbose_name(instance):
    """Retorna o nome legível do modelo (verbose_name) ou um fallback."""
    if hasattr(instance, '_meta') and hasattr(instance._meta, 'verbose_name'):
        return str(instance._meta.verbose_name).capitalize()
    return "Item"

def _get_instance_identifier(instance):
    """Retorna um identificador comum para a instância (nome, username, número, PK)."""
    if hasattr(instance, 'nome') and instance.nome:
        return instance.nome
    if hasattr(instance, 'razao_social') and instance.razao_social:
        return instance.razao_social
    if hasattr(instance, 'username') and instance.username:
        return instance.username
    if hasattr(instance, 'numero') and instance.numero: # Para NotaFiscal
        return instance.numero
    if hasattr(instance, 'pk') and instance.pk:
        return str(instance.pk)
    return "o item" # Fallback genérico

class AppMessages:
    """
    Classe utilitária para gerar e adicionar mensagens padronizadas.
    Instancie com o objeto request em cada view.
    """
    def __init__(self, request):
        self.request = request

    def success_created(self, instance, custom_message=None):
        """Mensagem para criação bem-sucedida de um objeto."""
        if custom_message:
            message = custom_message
        else:
            model_name = _get_model_verbose_name(instance)
            identifier = _get_instance_identifier(instance)
            message = f"{model_name} '{identifier}' criado(a) com sucesso!"
        messages.success(self.request, message)
        return message

    def success_updated(self, instance, custom_message=None):
        """Mensagem para atualização bem-sucedida de um objeto."""
        if custom_message:
            message = custom_message
        else:
            model_name = _get_model_verbose_name(instance)
            identifier = _get_instance_identifier(instance)
            message = f"{model_name} '{identifier}' atualizado(a) com sucesso!"
        messages.success(self.request, message)
        return message

    def success_deleted(self, model_name, identifier, custom_message=None):
        """Mensagem para exclusão bem-sucedida de um objeto."""
        if custom_message:
            message = custom_message
        else:
            message = f"{model_name.capitalize()} '{identifier}' excluído(a) com sucesso!"
        messages.success(self.request, message)
        return message

    def success_imported(self, instance, source_type="XML", custom_message=None):
        """Mensagem para importação bem-sucedida de um objeto."""
        if custom_message:
            message = custom_message
        else:
            model_name = _get_model_verbose_name(instance)
            identifier = _get_instance_identifier(instance)
            message = f"{model_name} '{identifier}' importado(a) via {source_type} com sucesso!"
        messages.success(self.request, message)
        return message

    def warning(self, message_text):
        """Mensagem de aviso."""
        message = f"Atenção: {message_text}"
        messages.warning(self.request, message)
        return message

    def info(self, message_text):
        """Mensagem informativa."""
        message = f"Informação: {message_text}"
        messages.info(self.request, message)
        return message

    def error(self, message_text):
        """Mensagem de erro."""
        message = message_text
        messages.error(self.request, message)
        return message

    def success_process(self, message_text):
        """Mensagem para um processo em lote bem-sucedido."""
        messages.success(self.request, message_text)
        return message_text

    # Adicione outros tipos de mensagens conforme necessário (ex: confirmation_sent, validation_error)

# Função auxiliar para obter a instância de AppMessages na view
def get_app_messages(request):
    return AppMessages(request)