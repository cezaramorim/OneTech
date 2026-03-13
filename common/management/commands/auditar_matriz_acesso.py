from django.core.management.base import BaseCommand

from common.access_matrix import ROUTE_PERMISSION_MATRIX
from common.menu_config import MENU_ITEMS


class Command(BaseCommand):
    help = 'Audita consistencia entre menu_config e access_matrix.'

    def _iter_items(self, items, trail=''):
        for item in items:
            name = item.get('name', '?')
            current = f"{trail} > {name}" if trail else name
            yield current, item
            children = item.get('children') or []
            if children:
                yield from self._iter_items(children, current)

    def handle(self, *args, **options):
        problems = []

        for path, item in self._iter_items(MENU_ITEMS):
            url_name = item.get('url_name')
            if not url_name or url_name == '#':
                continue

            is_exception = item.get('staff_only') or item.get('superuser_only')
            menu_perms = tuple(item.get('required_perms') or ())
            matrix_perms = tuple(ROUTE_PERMISSION_MATRIX.get(url_name, ()))

            if url_name not in ROUTE_PERMISSION_MATRIX:
                problems.append(f"AUSENTE_NA_MATRIZ: {path} ({url_name})")
                continue

            if menu_perms != matrix_perms:
                problems.append(
                    f"DIVERGENCIA: {path} ({url_name}) menu={menu_perms} matriz={matrix_perms}"
                )
                continue

            if not menu_perms and not is_exception:
                problems.append(f"SEM_PERMISSAO: {path} ({url_name})")

        if problems:
            self.stdout.write(self.style.ERROR('Foram encontradas inconsistencias:'))
            for line in problems:
                self.stdout.write(self.style.ERROR(f'- {line}'))
            raise SystemExit(1)

        self.stdout.write(self.style.SUCCESS('Matriz de acesso consistente com o menu.'))
