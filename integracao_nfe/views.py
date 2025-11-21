import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from nota_fiscal.models import NotaFiscal
from .services import emitir_nfe_api

@csrf_exempt
@require_POST
def sefaz_webhook(request):
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
        nota = NotaFiscal.objects.select_related('emitente', 'destinatario').get(pk=nota_id)

        # 1. Obter dados do emitente a partir do tenant atual (injetado pelo middleware)
        tenant_atual = request.tenant
        if not tenant_atual:
            return JsonResponse({'success': False, 'message': 'Nenhum cliente (tenant) ativo na sessão.'}, status=400)

        # Valida se o emitente da nota é o mesmo do tenant atual
        if nota.emitente != tenant_atual:
             return JsonResponse({'success': False, 'message': 'A nota fiscal não pertence ao cliente (tenant) ativo.'}, status=403)

        # Carrega o certificado e a senha do tenant
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