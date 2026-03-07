from django.core.management.base import BaseCommand
from django.db import transaction

from produto.models import NCM
from produto.models_fiscais import DetalhesFiscaisProduto
from produto.ncm_utils import normalizar_codigo_ncm


class Command(BaseCommand):
    help = 'Consolida NCMs duplicados por formatacao, mantendo um unico codigo normalizado.'

    def add_arguments(self, parser):
        parser.add_argument('--apply', action='store_true', help='Aplica as alteracoes no banco. Sem esta flag, executa em modo dry-run.')

    def handle(self, *args, **options):
        apply_changes = options['apply']
        duplicates = {}
        for ncm in NCM.objects.all().order_by('id'):
            normalized = normalizar_codigo_ncm(ncm.codigo)
            duplicates.setdefault(normalized, []).append(ncm)

        affected_groups = {k: v for k, v in duplicates.items() if k and len(v) > 1}
        if not affected_groups:
            self.stdout.write(self.style.SUCCESS('Nenhuma duplicidade de NCM encontrada.'))
            return

        self.stdout.write(self.style.WARNING(f'{len(affected_groups)} grupo(s) de NCM com duplicidade encontrado(s).'))

        for normalized, items in affected_groups.items():
            keeper = self._choose_keeper(items)
            others = [item for item in items if item.pk != keeper.pk]
            self.stdout.write(f'NCM {normalized}: manter ID {keeper.pk} ({keeper.codigo}) e consolidar {len(others)} duplicado(s).')

            if not apply_changes:
                continue

            with transaction.atomic():
                for duplicate in others:
                    DetalhesFiscaisProduto.objects.filter(ncm_id=duplicate.pk).update(ncm=keeper)
                    duplicate.delete()

                if keeper.codigo != normalized:
                    keeper.codigo = normalized
                    keeper.save(update_fields=['codigo'])

        if apply_changes:
            self.stdout.write(self.style.SUCCESS('Consolidacao de NCM concluida.'))
        else:
            self.stdout.write(self.style.WARNING('Dry-run concluido. Use --apply para persistir as alteracoes.'))

    def _choose_keeper(self, items):
        def score(item):
            descricao = (item.descricao or '').strip()
            placeholder = descricao.lower() == f'ncm {normalizar_codigo_ncm(item.codigo)}'.lower()
            return (placeholder, -len(descricao), item.pk)

        return sorted(items, key=score)[0]
