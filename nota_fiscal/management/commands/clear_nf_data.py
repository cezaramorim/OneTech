from django.core.management.base import BaseCommand
from nota_fiscal.models import NotaFiscal
from produto.models import Produto

class Command(BaseCommand):
    help = 'Deletes all NotaFiscal and Produto data from the database.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Deleting all NotaFiscal related data...'))
        NotaFiscal.objects.all().delete() # This should cascade delete ItemNotaFiscal, TransporteNotaFiscal, DuplicataNotaFiscal, and EntradaProduto
        self.stdout.write(self.style.SUCCESS('All NotaFiscal related data deleted.'))

        self.stdout.write(self.style.WARNING('Deleting all Produto data...'))
        Produto.objects.all().delete()
        self.stdout.write(self.style.SUCCESS('All Produto data deleted.'))

        self.stdout.write(self.style.SUCCESS('Database cleaned successfully!'))