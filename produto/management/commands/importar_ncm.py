from django.core.management.base import BaseCommand

from produto.ncm_services import import_ncm_from_local_json


class Command(BaseCommand):
    help = 'Importa ou atualiza os dados NCM a partir de um arquivo JSON local oficial da Receita.'

    def handle(self, *args, **options):
        try:
            result = import_ncm_from_local_json()
            self.stdout.write(self.style.SUCCESS(f"{result['count']} codigos NCM importados/atualizados com sucesso."))
        except FileNotFoundError:
            self.stderr.write(self.style.ERROR('Arquivo ncm.json nao encontrado em produto/data/.'))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Erro: {str(e)}'))
