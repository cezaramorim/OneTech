from django.core.management.base import BaseCommand
from empresas.models import CategoriaEmpresa
from django.db.models import Count

class Command(BaseCommand):
    help = 'Encontra e remove categorias de empresas duplicadas baseadas no nome'

    def handle(self, *args, **options):
        # Encontrar nomes de categorias duplicados
        nomes_duplicados = (
            CategoriaEmpresa.objects.values('nome')
            .annotate(count=Count('id'))
            .filter(count__gt=1)
            .values_list('nome', flat=True)
        )

        for nome in nomes_duplicados:
            if not nome:  # Ignorar nomes vazios
                continue
            categorias = CategoriaEmpresa.objects.filter(nome=nome).order_by('id')
            categoria_original = categorias.first()
            self.stdout.write(self.style.SUCCESS(f'Mantendo categoria {categoria_original.id} para o nome "{nome}"'
            ))
            for categoria_duplicada in categorias[1:]:
                self.stdout.write(self.style.WARNING(f'Removendo categoria duplicada {categoria_duplicada.id}'))
                categoria_duplicada.delete()

        self.stdout.write(self.style.SUCCESS('Verificação de categorias duplicadas concluída.'))
