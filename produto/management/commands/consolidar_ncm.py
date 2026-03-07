from django.core.management.base import BaseCommand

from produto.ncm_services import consolidate_ncm_duplicates, inspect_ncm_duplicates


class Command(BaseCommand):
    help = 'Consolida NCMs duplicados por formatacao, mantendo um unico codigo normalizado.'

    def add_arguments(self, parser):
        parser.add_argument('--apply', action='store_true', help='Aplica as alteracoes no banco. Sem esta flag, executa em modo dry-run.')

    def handle(self, *args, **options):
        apply_changes = options['apply']
        summary = consolidate_ncm_duplicates() if apply_changes else inspect_ncm_duplicates()

        if not summary['groups']:
            self.stdout.write(self.style.SUCCESS('Nenhuma duplicidade de NCM encontrada.'))
            return

        self.stdout.write(self.style.WARNING(f"{summary['group_count']} grupo(s) de NCM com duplicidade encontrado(s)."))
        for group in summary['groups']:
            self.stdout.write(
                f"NCM {group['normalized_code']}: manter ID {group['keeper_id']} ({group['keeper_codigo']}) e consolidar {group['duplicate_count']} duplicado(s)."
            )

        if apply_changes:
            self.stdout.write(self.style.SUCCESS('Consolidacao de NCM concluida.'))
        else:
            self.stdout.write(self.style.WARNING('Dry-run concluido. Use --apply para persistir as alteracoes.'))
