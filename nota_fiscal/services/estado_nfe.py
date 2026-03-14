from django.utils import timezone


STATUS_RASCUNHO = 'rascunho'
STATUS_VALIDADA = 'validada'
STATUS_ENVIADA = 'enviada'
STATUS_AUTORIZADA = 'autorizada'
STATUS_REJEITADA = 'rejeitada'
STATUS_CANCELADA = 'cancelada'

STATUS_VALIDOS = {
    STATUS_RASCUNHO,
    STATUS_VALIDADA,
    STATUS_ENVIADA,
    STATUS_AUTORIZADA,
    STATUS_REJEITADA,
    STATUS_CANCELADA,
}

TRANSICOES = {
    STATUS_RASCUNHO: {STATUS_VALIDADA, STATUS_CANCELADA},
    STATUS_VALIDADA: {STATUS_ENVIADA, STATUS_CANCELADA},
    STATUS_ENVIADA: {STATUS_AUTORIZADA, STATUS_REJEITADA, STATUS_CANCELADA},
    STATUS_REJEITADA: {STATUS_VALIDADA, STATUS_CANCELADA},
    STATUS_AUTORIZADA: {STATUS_CANCELADA},
    STATUS_CANCELADA: set(),
}


def normalizar_status_externo(status):
    raw = (status or '').strip().lower()
    mapa = {
        'autorizada': STATUS_AUTORIZADA,
        'autorizado': STATUS_AUTORIZADA,
        'rejeitada': STATUS_REJEITADA,
        'rejeitado': STATUS_REJEITADA,
        'cancelada': STATUS_CANCELADA,
        'cancelado': STATUS_CANCELADA,
        'processando': STATUS_ENVIADA,
        'recebida': STATUS_ENVIADA,
        'enviada': STATUS_ENVIADA,
        'validada': STATUS_VALIDADA,
        'rascunho': STATUS_RASCUNHO,
    }
    return mapa.get(raw, raw)


def _status_atual(nota):
    return (nota.status_sefaz or '').strip().lower()


def pode_transicionar(status_origem, status_destino):
    origem = (status_origem or '').strip().lower()
    destino = (status_destino or '').strip().lower()

    if destino not in STATUS_VALIDOS:
        return False
    if origem == destino:
        return True
    if not origem:
        return destino in {STATUS_RASCUNHO, STATUS_VALIDADA}
    if origem not in TRANSICOES:
        return False
    return destino in TRANSICOES[origem]


def aplicar_status_nfe(
    nota,
    novo_status,
    *,
    motivo='',
    protocolo=None,
    id_servico_terceiro=None,
    data_autorizacao=None,
    force=False,
):
    destino = normalizar_status_externo(novo_status)
    origem = _status_atual(nota)

    if not force and not pode_transicionar(origem, destino):
        return False, f'Transicao de status invalida: {origem or "vazio"} -> {destino}'

    nota.status_sefaz = destino
    if motivo:
        nota.motivo_status_sefaz = motivo
    if protocolo:
        nota.protocolo_autorizacao = protocolo
    if id_servico_terceiro:
        nota.id_servico_terceiro = id_servico_terceiro
    if data_autorizacao:
        nota.data_autorizacao = data_autorizacao
    elif destino == STATUS_AUTORIZADA and nota.data_autorizacao is None:
        nota.data_autorizacao = timezone.now()

    nota.save()
    return True, ''

