import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from nota_fiscal.models import NotaFiscal

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