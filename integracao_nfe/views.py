import json
import hmac
import hashlib
import logging
import time
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from nota_fiscal.models import NotaFiscal
from control.models import Emitente
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
        digestmod=hashlib.sha256
    ).hexdigest().lower()

    if not hmac.compare_digest(expected_signature, received_signature):
        return False, 'Assinatura invalida.'

    return True, ''

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
        
        # Exemplo de como você pode extrair os dados do payload
        # Adapte isso para o formato real do webhook da SEFAZ ou do serviço de terceiros
        chave_acesso = payload.get('chave_acesso')
        status = payload.get('status')
        protocolo = payload.get('protocolo')
        motivo = payload.get('motivo', '')
        data_autorizacao = payload.get('data_autorizacao') # Pode precisar de formatação

        if not chave_acesso or not status:
            return JsonResponse({'status': 'erro', 'mensagem': 'Dados mínimos (chave_acesso, status) não fornecidos.'}, status=400)

        try:
            nota_fiscal = NotaFiscal.objects.get(chave_acesso=chave_acesso)
            nota_fiscal.status_sefaz = status
            nota_fiscal.protocolo_autorizacao = protocolo
            nota_fiscal.motivo_status_sefaz = motivo
            # TODO: Converter data_autorizacao para datetime object se necessário
            # nota_fiscal.data_autorizacao = ...
            nota_fiscal.save()
            return JsonResponse({'status': 'sucesso', 'mensagem': f'Nota Fiscal {chave_acesso} atualizada para {status}.'})
        except NotaFiscal.DoesNotExist:
            return JsonResponse({'status': 'erro', 'mensagem': f'Nota Fiscal com chave {chave_acesso} não encontrada.'}, status=404)

    except json.JSONDecodeError:
        return JsonResponse({'status': 'erro', 'mensagem': 'Payload JSON inválido.'}, status=400)
    except Exception as e:
        return JsonResponse({'status': 'erro', 'mensagem': f'Erro interno do servidor: {str(e)}'}, status=500)


@login_required
@require_POST
def emitir_nota_fiscal_view(request):
    """
    Recebe o ID de uma nota fiscal, busca os dados do tenant atual (emitente),
    monta um payload e chama o serviço (simulado) de emissão de NF-e.
    """
    try:
        data = json.loads(request.body)
        nota_id = data.get('nota_id')
        nota = NotaFiscal.objects.select_related('emitente_proprio', 'destinatario').get(pk=nota_id)

        # 1. Obter dados do emitente a partir do tenant atual (injetado pelo middleware)
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

        # Valida se o emitente da nota e o mesmo emitente ativo do tenant atual
        if nota.emitente_proprio_id != emitente_ativo_id:
            return JsonResponse({'success': False, 'message': 'A nota fiscal nao pertence a empresa ativa do tenant.', 'code': 'permission_denied'}, status=403)

        # Carrega o certificado e a senha quando houver tenant ativo no contexto
        if not tenant_atual:
            return JsonResponse({'success': False, 'message': 'Emissao no dominio default exige tenant/empresa ativa com certificado configurado.'}, status=400)

        try:
            certificado_pfx = tenant_atual.certificado_a1.read()
            senha_certificado = tenant_atual.senha_certificado
        except (ValueError, FileNotFoundError):
             return JsonResponse({'success': False, 'message': 'Certificado digital do cliente não encontrado ou inválido.'}, status=400)

        # 2. Montar o payload da nota com base no objeto 'nota'
        # Esta é uma simplificação. Um payload real para a SEFAZ é muito mais complexo.
        payload_nfe = {
            "emitente": {
                "cnpj": tenant_atual.cnpj,
                "razao_social": tenant_atual.razao_social,
            },
            "destinatario": {
                "cnpj": nota.destinatario.cnpj if nota.destinatario else '',
                "nome": nota.destinatario.razao_social if nota.destinatario else '',
            },
            "produtos": [
                {"nome": item.descricao, "valor": float(item.valor_total)}
                for item in nota.itens.all()
            ],
            "valor_total": float(nota.valor_total_nota),
        }

        # 3. Chamar o serviço de emissão (simulado)
        resultado_api = emitir_nfe_api(payload_nfe, certificado_pfx, senha_certificado)

        # 4. Atualizar o status da nota localmente com base na resposta da API
        if resultado_api.get('success'):
            nota.status_sefaz = 'processando'
            nota.id_servico_terceiro = resultado_api.get('id_externo')
            nota.save()
            return JsonResponse({'success': True, 'message': 'Nota enviada para processamento.'})
        else:
            return JsonResponse({'success': False, 'message': f"Erro na API de emissão: {resultado_api.get('error')}"})

    except NotaFiscal.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Nota Fiscal não encontrada.'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Erro interno: {str(e)}'}, status=500)
