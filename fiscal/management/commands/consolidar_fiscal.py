from django.core.management.base import BaseCommand, CommandError

from fiscal.fiscal_services import consolidate_duplicates, inspect_duplicates


class Command(BaseCommand):
    help = 'Inspeciona ou consolida duplicidades em CFOP e Natureza de Opera\u00e7\u00e3o.'

    def add_arguments(self, parser):
        parser.add_argument('--type', required=True, choices=['cfop', 'natureza_operacao'])
        parser.add_argument('--apply', action='store_true')

    def handle(self, *args, **options):
        data_type = options['type']
        try:
            summary = consolidate_duplicates(data_type) if options['apply'] else inspect_duplicates(data_type)
        except Exception as exc:
            raise CommandError(str(exc)) from exc

        if summary['group_count'] == 0:
            self.stdout.write(self.style.SUCCESS('Nenhuma duplicidade encontrada.'))
            return

        self.stdout.write(self.style.WARNING(f"{summary['group_count']} grupo(s) com duplicidade encontrado(s)."))
        for group in summary['groups']:
            self.stdout.write(f"- {group['key']}: manter ID {group['keeper_id']} e tratar {group['count']} duplicado(s).")

        if options['apply']:
            self.stdout.write(self.style.SUCCESS('Consolida\u00e7\u00e3o conclu\u00edda.'))
