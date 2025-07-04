# fiscal/utils.py

import pandas as pd
from django.db import transaction
from .models import Cfop, NaturezaOperacao

def import_cfop_from_excel(file_obj):
    """
    Processa um arquivo Excel (em memória ou físico) e importa os dados de CFOP.

    Args:
        file_obj: Um objeto de arquivo (por exemplo, UploadedFile do Django) contendo os dados do Excel.

    Returns:
        Um dicionário com as chaves "success" (bool) e "message" (str) indicando o resultado da operação.
    """
    try:
        # Usar openpyxl explicitamente para ler o conteúdo do arquivo
        df = pd.read_excel(file_obj, engine='openpyxl')

        # Verifica se as colunas obrigatórias estão presentes no arquivo Excel.
        required_columns = ['codigo', 'descricao']
        if not all(col in df.columns for col in required_columns):
            missing = ", ".join([col for col in required_columns if col not in df.columns])
            return {"success": False, "message": f"As seguintes colunas obrigatórias não foram encontradas: {missing}."}

        with transaction.atomic():
            # Itera sobre cada linha do DataFrame para criar ou atualizar objetos Cfop.
            for index, row in df.iterrows():
                codigo = str(row['codigo']).strip()
                descricao = str(row['descricao']).strip()
                categoria = str(row.get('categoria', '')).strip()

                if not codigo or not descricao:
                    # Ignora linhas que não possuem código ou descrição, pois são essenciais.
                    continue

                # Usa update_or_create para evitar duplicatas e atualizar dados existentes.
                Cfop.objects.update_or_create(
                    codigo=codigo,
                    defaults={'descricao': descricao, 'categoria': categoria}
                )
        return {"success": True, "message": "Importação de CFOPs concluída com sucesso!"}
    except Exception as e:
        return {"success": False, "message": f"Ocorreu um erro ao processar o arquivo: {e}"}


def import_natureza_operacao_from_excel(file_obj):
    """
    Processa um arquivo Excel e importa os dados de Natureza de Operação.

    Args:
        file_obj: Um objeto de arquivo (por exemplo, UploadedFile do Django) contendo os dados do Excel.

    Returns:
        Um dicionário com as chaves "success" (bool) e "message" (str) indicando o resultado da operação.
    """
    try:
        df = pd.read_excel(file_obj, engine='openpyxl')
        
        # Verifica se as colunas obrigatórias estão presentes no arquivo Excel.
        required_columns = ['descricao']
        if not all(col in df.columns for col in required_columns):
            missing = ", ".join([col for col in required_columns if col not in df.columns])
            return {"success": False, "message": f"As seguintes colunas obrigatórias não foram encontradas: {missing}."}

        with transaction.atomic():
            # Itera sobre cada linha do DataFrame para criar ou atualizar objetos NaturezaOperacao.
            for index, row in df.iterrows():
                descricao = str(row['descricao']).strip()
                if not descricao:
                    # Ignora linhas que não possuem descrição, pois é essencial.
                    continue

                # Usa update_or_create para evitar duplicatas e atualizar dados existentes.
                NaturezaOperacao.objects.update_or_create(
                    descricao=descricao,
                    defaults={
                        'codigo': str(row.get('codigo', '')).strip(),
                        'observacoes': str(row.get('observacoes', '')).strip()
                    }
                )
        return {"success": True, "message": "Importação de Naturezas de Operação concluída com sucesso!"}
    except Exception as e:
        return {"success": False, "message": f"Ocorreu um erro ao processar o arquivo: {e}"}
