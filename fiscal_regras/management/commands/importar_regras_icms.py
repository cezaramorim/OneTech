import json

from django.core.management.base import BaseCommand, CommandError

from fiscal_regras.models import RegraAliquotaICMS


class Command(BaseCommand):
    help = 'Importa regras ICMS a partir de um arquivo JSON.'

    def add_arguments(self, parser):
        parser.add_argument('--file', required=True, help='Caminho para o arquivo JSON.')

    def handle(self, *args, **options):
        path = options['file']
        try:
            with open(path, 'r', encoding='utf-8') as fp:
                payload = json.load(fp)
        except Exception as exc:
            raise CommandError(f'Nao foi possivel ler arquivo: {exc}')

        if not isinstance(payload, list):
            raise CommandError('Arquivo invalido: JSON deve ser uma lista de objetos.')

        created = 0
        updated = 0
        for item in payload:
            defaults = {k: v for k, v in item.items() if k != 'ncm_prefixo'}
            _, was_created = RegraAliquotaICMS.objects.update_or_create(
                ncm_prefixo=item.get('ncm_prefixo'),
                descricao=item.get('descricao', ''),
                defaults=defaults,
            )
            if was_created:
                created += 1
            else:
                updated += 1

        self.stdout.write(self.style.SUCCESS(f'Importacao concluida. Criadas: {created}. Atualizadas: {updated}.'))
