from django.db import connections, DEFAULT_DB_ALIAS
from control.models import Tenant
import MySQLdb
import sys

def run():
    print("Iniciando processo de limpeza para o tenant 'aquatech' via runscript...")

    try:
        # Passo 1: Excluir o registro do Tenant do banco de dados de controle.
        tenant_slug = 'aquatech'
        deleted_count, _ = Tenant.objects.filter(slug=tenant_slug).delete()
        if deleted_count > 0:
            print(f"Registro do tenant com slug '{tenant_slug}' excluído com sucesso.")
        else:
            print(f"Nenhum registro de tenant encontrado para o slug '{tenant_slug}'.")

        # Passo 2: Excluir o banco de dados do tenant.
        db_name = 'onetech_aquatech'
        default_db_conn_settings = connections[DEFAULT_DB_ALIAS].settings_dict
        
        conn = MySQLdb.connect(
            host=default_db_conn_settings['HOST'],
            user=default_db_conn_settings['USER'],
            passwd=default_db_conn_settings['PASSWORD'],
            port=int(default_db_conn_settings['PORT']),
        )
        cursor = conn.cursor()
        print(f"Tentando excluir o banco de dados `{db_name}`...")
        cursor.execute(f"DROP DATABASE IF EXISTS `{db_name}`")
        print(f"Comando DROP DATABASE para `{db_name}` executado com sucesso.")
        cursor.close()
        conn.close()

        print("Processo de limpeza concluído com sucesso.")

    except Exception as e:
        print(f"Ocorreu um erro durante a limpeza: {e}", file=sys.stderr)
        raise e
