from django.core.management.base import BaseCommand
from empresas.models import Empresa
from django.db.models import Count

class Command(BaseCommand):
    help = 'Encontra e remove empresas duplicadas baseadas no CNPJ e CPF'

    def handle(self, *args, **options):
        # Encontrar CNPJs duplicados
        cnpjs_duplicados = (
            Empresa.objects.values('cnpj')
            .annotate(count=Count('id'))
            .filter(count__gt=1)
            .values_list('cnpj', flat=True)
        )

        for cnpj in cnpjs_duplicados:
            if not cnpj:  # Ignorar CNPJs vazios
                continue
            empresas = Empresa.objects.filter(cnpj=cnpj).order_by('id')
            empresa_original = empresas.first()
            self.stdout.write(self.style.SUCCESS(f'Mantendo empresa {empresa_original.id} para o CNPJ {cnpj}'))
            for empresa_duplicada in empresas[1:]:
                self.stdout.write(self.style.WARNING(f'Removendo empresa duplicada {empresa_duplicada.id}'))
                empresa_duplicada.delete()

        # Encontrar CPFs duplicados
        cpfs_duplicados = (
            Empresa.objects.values('cpf')
            .annotate(count=Count('id'))
            .filter(count__gt=1)
            .values_list('cpf', flat=True)
        )

        for cpf in cpfs_duplicados:
            if not cpf:  # Ignorar CPFs vazios
                continue
            empresas = Empresa.objects.filter(cpf=cpf).order_by('id')
            empresa_original = empresas.first()
            self.stdout.write(self.style.SUCCESS(f'Mantendo empresa {empresa_original.id} para o CPF {cpf}'))
            for empresa_duplicada in empresas[1:]:
                self.stdout.write(self.style.WARNING(f'Removendo empresa duplicada {empresa_duplicada.id}'))
                empresa_duplicada.delete()

        self.stdout.write(self.style.SUCCESS('Verificacao de duplicatas concluida.'))
