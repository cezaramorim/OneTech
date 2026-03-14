import hashlib
import hmac
import json
import logging
import time

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from accounts.utils.decorators import login_required_json, permission_required_json
from control.models import Emitente
from nota_fiscal.models import NotaFiscal
from nota_fiscal.services.estado_nfe import (
    STATUS_ENVIADA,
    STATUS_VALIDADA,
    aplicar_status_nfe,
    normalizar_status_externo,
)
from nota_fiscal.services.pre_emissao import validar_nota_pre_emissao

from .services import emitir_nfe_api

logger = logging.getLogger(__name__)


def _validate_webhook_signature(request):
    # Headers esperados:
    # - X-OneTech-Timestamp: epoch seconds
    # - X-OneTech-Signature: hex sha256(secret, f"{timestamp}.{payload}")
    secret = (getattr(settings, 'NFE_WEBHOOK_SECRET', '') or '').strip()
    if not secret:
        return False, 'Segredo de webhook nao configurado.'

    raw_timestamp = (request.headers.get('X-OneTech-Timestamp') or '').strip()
    received_signature = (request.headers.get('X-OneTech-Signature') or '').strip().lower()

    if not raw_timestamp or not received_signature:
        return False, 'Headers de autenticacao ausentes.'

    try:
        timestamp = int(raw_timestamp)
    except ValueError:
        return False, 'Timestamp invalido.'

    tolerance = int(getattr(settings, 'NFE_WEBHOOK_TOLERANCE_SECONDS', 300) or 300)
    now = int(time.time())
    if abs(now - timestamp) > tolerance:
        return False, 'Timestamp expirado.'

    signed_payload = f'{raw_timestamp}.'.encode('utf-8') + request.body
    expected_signature = hmac.new(
        key=secret.encode('utf-8'),
        msg=signed_payload,
        digestmod=hashlib.sha256,
    ).hexdigest().lower()

    if not hmac.compare_digest(expected_signature, received_signature):
        return False, 'Assinatura invalida.'

    return True, ''


def _parse_data_autorizacao(valor):
    if not valor:
        return None
    if hasattr(valor, 'year'):
        return valor
    if isinstance(valor, str):
        parsed = parse_datetime(valor)
        return parsed
    return None


@csrf_exempt
@require_POST
def sefaz_webhook(request):
    is_valid, reason = _validate_webhook_signature(request)
    if not is_valid:
        logger.warning(
            'Webhook NFe rejeitado: %s | ip=%s host=%s',
            reason,
            request.META.get('REMOTE_ADDR'),
            request.get_host(),
        )
        return JsonResponse({'status': 'erro', 'mensagem': 'Webhook nao autorizado.'}, status=401)

    try:
        payload = json.loads(request.body.decode('utf-8'))
        chave_acesso = payload.get('chave_acesso')
        status = payload.get('status')
        protocolo = payload.get('protocolo')
        motivo = payload.get('motivo', '')
        data_autorizacao = _parse_data_autorizacao(payload.get('data_autorizacao'))

        if not chave_acesso or not status:
            return JsonResponse(
                {'status': 'erro', 'mensagem': 'Dados minimos (chave_acesso, status) nao fornecidos.'},
                status=400,
            )

        try:
            nota_fiscal = NotaFiscal.objects.get(chave_acesso=chave_acesso)
        except NotaFiscal.DoesNotExist:
            return JsonResponse(
                {'status': 'erro', 'mensagem': f'Nota Fiscal com chave {chave_acesso} nao encontrada.'},
                status=404,
            )

        status_normalizado = normalizar_status_externo(status)
        ok, erro_transicao = aplicar_status_nfe(
            nota_fiscal,
            status_normalizado,
            motivo=motivo,
            protocolo=protocolo,
            data_autorizacao=data_autorizacao,
        )
        if not ok:
            return JsonResponse({'status': 'erro', 'mensagem': erro_transicao}, status=409)

        return JsonResponse(
            {
                'status': 'sucesso',
                'mensagem': f'Nota Fiscal {chave_acesso} atualizada para {status_normalizado}.',
            }
        )

    except json.JSONDecodeError:
        return JsonResponse({'status': 'erro', 'mensagem': 'Payload JSON invalido.'}, status=400)
    except Exception as e:
        return JsonResponse({'status': 'erro', 'mensagem': f'Erro interno do servidor: {str(e)}'}, status=500)


@login_required_json
@permission_required_json('integracao_nfe.can_emit_nfe', raise_exception=True)
@require_POST
def emitir_nota_fiscal_view(request):
    """
    Recebe o ID de uma nota fiscal, busca os dados do tenant atual (emitente),
    monta um payload e chama o servico (simulado) de emissao de NF-e.
    """
    try:
        data = json.loads(request.body)
        nota_id = data.get('nota_id')
        nota = NotaFiscal.objects.select_related('emitente_proprio', 'destinatario').get(pk=nota_id)

        tenant_atual = getattr(request, 'tenant', None)

        emitente_ativo_id = getattr(tenant_atual, 'emitente_padrao_id', None)
        if not emitente_ativo_id:
            emitente_ativo_id = Emitente.objects.filter(is_default=True).values_list('id', flat=True).first()
        if not emitente_ativo_id:
            emitente_ativo_id = nota.emitente_proprio_id
        if not emitente_ativo_id:
            return JsonResponse({'success': False, 'message': 'Nenhuma empresa ativa definida para emissao.'}, status=400)

        if nota.tipo_operacao != '1':
            return JsonResponse({'success': False, 'message': 'Apenas notas de saida podem ser emitidas nesta tela.'}, status=400)

        pre = validar_nota_pre_emissao(nota)
        nota.pre_emissao_ok = bool(pre.get('ok'))
        nota.pre_emissao_validada_em = timezone.now()
        nota.pre_emissao_snapshot = pre
        nota.save(update_fields=['pre_emissao_ok', 'pre_emissao_validada_em', 'pre_emissao_snapshot'])

        if not pre.get('ok'):
            return JsonResponse(
                {
                    'success': False,
                    'message': 'Nota reprovada no gate de pre-emissao.',
                    'errors': pre.get('errors', []),
                    'warnings': pre.get('warnings', []),
                    'snapshot': pre.get('snapshot', {}),
                },
                status=400,
            )

        ok_validada, erro_validada = aplicar_status_nfe(nota, STATUS_VALIDADA)
        if not ok_validada:
            return JsonResponse({'success': False, 'message': erro_validada}, status=409)

        if nota.emitente_proprio_id != emitente_ativo_id:
            return JsonResponse(
                {
                    'success': False,
                    'message': 'A nota fiscal nao pertence a empresa ativa do tenant.',
                    'code': 'permission_denied',
                },
                status=403,
            )

        if not tenant_atual:
            return JsonResponse(
                {
                    'success': False,
                    'message': 'Emissao no dominio default exige tenant/empresa ativa com certificado configurado.',
                },
                status=400,
            )

        try:
            certificado_pfx = tenant_atual.certificado_a1.read()
            senha_certificado = tenant_atual.senha_certificado
        except (ValueError, FileNotFoundError):
            return JsonResponse(
                {
                    'success': False,
                    'message': 'Certificado digital do cliente nao encontrado ou invalido.',
                },
                status=400,
            )

        payload_nfe = {
            'emitente': {
                'cnpj': tenant_atual.cnpj,
                'razao_social': tenant_atual.razao_social,
            },
            'destinatario': {
                'cnpj': nota.destinatario.cnpj if nota.destinatario else '',
                'nome': nota.destinatario.razao_social if nota.destinatario else '',
            },
            'produtos': [
                {'nome': item.descricao, 'valor': float(item.valor_total)}
                for item in nota.itens.all()
            ],
            'valor_total': float(nota.valor_total_nota),
        }

        resultado_api = emitir_nfe_api(payload_nfe, certificado_pfx, senha_certificado)

        if resultado_api.get('success'):
            ok_enviada, erro_enviada = aplicar_status_nfe(
                nota,
                STATUS_ENVIADA,
                id_servico_terceiro=resultado_api.get('id_externo'),
            )
            if not ok_enviada:
                return JsonResponse({'success': False, 'message': erro_enviada}, status=409)
            return JsonResponse({'success': True, 'message': 'Nota enviada para processamento.'})

        return JsonResponse({'success': False, 'message': f"Erro na API de emissao: {resultado_api.get('error')}"})

    except NotaFiscal.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Nota Fiscal nao encontrada.'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Erro interno: {str(e)}'}, status=500)
