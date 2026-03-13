from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Executa auditoria consolidada de seguranca (matriz + baseline).'

    def add_arguments(self, parser):
        parser.add_argument('--strict', action='store_true', help='Executa baseline em modo estrito (gate de producao).')

    def handle(self, *args, **options):
        strict_mode = bool(options.get('strict'))

        self.stdout.write(self.style.NOTICE('Iniciando auditoria consolidada de seguranca...'))

        self.stdout.write('1/2 - Validando consistencia menu x matriz...')
        call_command('auditar_matriz_acesso')

        self.stdout.write('2/2 - Validando baseline de seguranca...')
        if strict_mode:
            call_command('validar_baseline_seguranca', '--strict')
        else:
            call_command('validar_baseline_seguranca')

        self.stdout.write(self.style.SUCCESS('Auditoria consolidada de seguranca concluida com sucesso.'))