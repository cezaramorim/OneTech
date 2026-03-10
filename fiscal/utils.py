from .fiscal_services import update_local_data_from_excel


def import_cfop_from_excel(file_obj):
    """Compatibilidade: atualiza a base local de CFOP a partir de Excel."""
    try:
        payload = update_local_data_from_excel(file_obj, 'cfop')
        count = payload['metadata']['item_count']
        return {'success': True, 'message': f'Base local de CFOP atualizada com sucesso. {count} registro(s) salvos em disco.'}
    except Exception as exc:
        return {'success': False, 'message': f'Ocorreu um erro ao processar o arquivo: {exc}'}


def import_natureza_operacao_from_excel(file_obj):
    """Compatibilidade: atualiza a base local de Natureza de Opera\u00e7\u00e3o a partir de Excel."""
    try:
        payload = update_local_data_from_excel(file_obj, 'natureza_operacao')
        count = payload['metadata']['item_count']
        return {'success': True, 'message': f'Base local de Natureza de Opera\u00e7\u00e3o atualizada com sucesso. {count} registro(s) salvos em disco.'}
    except Exception as exc:
        return {'success': False, 'message': f'Ocorreu um erro ao processar o arquivo: {exc}'}
