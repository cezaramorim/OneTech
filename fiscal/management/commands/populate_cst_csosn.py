from django.core.management.base import BaseCommand
from fiscal.models import CST, CSOSN

class Command(BaseCommand):
    help = 'Popula o banco de dados com códigos CST e CSOSN comuns.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Iniciando a população de CSTs e CSOSNs...'))

        # Códigos CST (Tabela A e B do ICMS)
        csts_data = [
            ('00', 'Tributada integralmente'),
            ('10', 'Tributada e com cobrança do ICMS por substituição tributária'),
            ('20', 'Com redução de base de cálculo'),
            ('30', 'Isenta ou não tributada e com cobrança do ICMS por substituição tributária'),
            ('40', 'Isenta'),
            ('41', 'Não tributada'),
            ('50', 'Suspensão'),
            ('51', 'Diferimento'),
            ('60', 'ICMS cobrado anteriormente por substituição tributária'),
            ('70', 'Com redução de base de cálculo e cobrança do ICMS por substituição tributária'),
            ('90', 'Outras'),
        ]

        for codigo, descricao in csts_data:
            cst, created = CST.objects.update_or_create(
                codigo=codigo,
                defaults={'descricao': descricao}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'CST {codigo} - {descricao} criado.'))
            else:
                self.stdout.write(self.style.WARNING(f'CST {codigo} - {descricao} já existe (atualizado).'))

        # Códigos CSOSN (Simples Nacional)
        csosns_data = [
            ('101', 'Tributada pelo Simples Nacional com permissão de crédito'),
            ('102', 'Tributada pelo Simples Nacional sem permissão de crédito'),
            ('103', 'Isenção do ICMS no Simples Nacional para faixa de receita bruta'),
            ('201', 'Tributada pelo Simples Nacional com permissão de crédito e com cobrança do ICMS por substituição tributária'),
            ('202', 'Tributada pelo Simples Nacional sem permissão de crédito e com cobrança do ICMS por substituição tributária'),
            ('203', 'Isenção do ICMS no Simples Nacional para faixa de receita bruta e com cobrança do ICMS por substituição tributária'),
            ('300', 'Imune'),
            ('400', 'Não tributada pelo Simples Nacional'),
            ('500', 'ICMS cobrado anteriormente por substituição tributária ou por antecipação'),
            ('900', 'Outros'),
        ]

        for codigo, descricao in csosns_data:
            csosn, created = CSOSN.objects.update_or_create(
                codigo=codigo,
                defaults={'descricao': descricao}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'CSOSN {codigo} - {descricao} criado.'))
            else:
                self.stdout.write(self.style.WARNING(f'CSOSN {codigo} - {descricao} já existe (atualizado).'))

        self.stdout.write(self.style.SUCCESS('População de CSTs e CSOSNs concluída com sucesso!'))
