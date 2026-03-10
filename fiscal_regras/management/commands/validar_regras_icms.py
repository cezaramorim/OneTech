from django.core.management.base import BaseCommand
from django.db.models import Count

from fiscal_regras.models import RegraAliquotaICMS


class Command(BaseCommand):
    help = 'Valida inconsistencias basicas de regras ICMS.'

    def handle(self, *args, **options):
        conflitos = (
            RegraAliquotaICMS.objects.values(
                'ncm_prefixo', 'tipo_operacao', 'modalidade', 'uf_origem', 'uf_destino', 'vigencia_inicio', 'vigencia_fim'
            )
            .annotate(total=Count('id'))
            .filter(total__gt=1)
        )

        if not conflitos.exists():
            self.stdout.write(self.style.SUCCESS('Nenhum conflito basico encontrado.'))
            return

        self.stdout.write(self.style.WARNING(f'Foram encontrados {conflitos.count()} grupo(s) com possivel conflito.'))
        for c in conflitos[:50]:
            self.stdout.write(str(c))
