from django.core.management.base import BaseCommand, CommandError

from fiscal.fiscal_services import import_local_data_to_db


class Command(BaseCommand):
    help = 'Importa CFOP ou Natureza de Opera\u00e7\u00e3o a partir da base local em JSON.'

    def add_arguments(self, parser):
        parser.add_argument('--type', required=True, choices=['cfop', 'natureza_operacao'])

    def handle(self, *args, **options):
        data_type = options['type']
        try:
            result = import_local_data_to_db(data_type)
        except FileNotFoundError as exc:
            raise CommandError(f'Arquivo local n?o encontrado: {exc}') from exc
        except Exception as exc:
            raise CommandError(str(exc)) from exc

        self.stdout.write(self.style.SUCCESS(f"{result['count']} registro(s) importados/atualizados para {data_type}."))
