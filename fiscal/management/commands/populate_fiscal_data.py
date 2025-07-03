from django.core.management.base import BaseCommand
from fiscal.models import Cfop, NaturezaOperacao

class Command(BaseCommand):
    help = 'Popula o banco de dados com dados iniciais de CFOPs e Naturezas de Operação.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Iniciando a população de dados fiscais...'))

        # Dados de CFOPs
        cfops_data = [
            {'codigo': '1102', 'descricao': 'Compra para comercialização'},
            {'codigo': '1403', 'descricao': 'Compra para comercialização em operação com mercadoria sujeita ao regime de substituição tributária'},
            {'codigo': '2102', 'descricao': 'Compra para comercialização (fora do estado)'},
            {'codigo': '5102', 'descricao': 'Venda de mercadoria adquirida ou recebida de terceiros para industrialização ou comercialização'},
            {'codigo': '5405', 'descricao': 'Venda de mercadoria adquirida ou recebida de terceiros em operação com mercadoria sujeita ao regime de substituição tributária, na condição de contribuinte substituído'},
            {'codigo': '6102', 'descricao': 'Venda de mercadoria adquirida ou recebida de terceiros para industrialização ou comercialização (fora do estado)'},
            {'codigo': '5900', 'descricao': 'Outras saídas de mercadorias ou prestações de serviços não especificadas'},
            {'codigo': '1900', 'descricao': 'Outras entradas de mercadorias ou aquisições de serviços não especificadas'},
        ]

        for data in cfops_data:
            cfop, created = Cfop.objects.update_or_create(
                codigo=data['codigo'],
                defaults={'descricao': data['descricao']}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'CFOP {cfop.codigo} - {cfop.descricao} criado.'))
            else:
                self.stdout.write(self.style.WARNING(f'CFOP {cfop.codigo} - {cfop.descricao} atualizado.'))

        self.stdout.write(self.style.SUCCESS('CFOPs populados com sucesso!'))

        # Dados de Naturezas de Operação
        naturezas_data = [
            {'descricao': 'Venda de Mercadoria', 'codigo': 'VENDA'},
            {'descricao': 'Devolução de Venda', 'codigo': 'DEV_VENDA'},
            {'descricao': 'Remessa para Industrialização', 'codigo': 'REM_IND'},
            {'descricao': 'Retorno de Industrialização', 'codigo': 'RET_IND'},
            {'descricao': 'Transferência de Mercadoria', 'codigo': 'TRANSF'},
            {'descricao': 'Simples Remessa', 'codigo': 'SIMP_REM'},
            {'descricao': 'Compra para Comercialização', 'codigo': 'COMPRA'},
            {'descricao': 'Devolução de Compra', 'codigo': 'DEV_COMPRA'},
        ]

        for data in naturezas_data:
            natureza, created = NaturezaOperacao.objects.update_or_create(
                descricao=data['descricao'],
                defaults={'codigo': data['codigo']}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Natureza de Operação "{natureza.descricao}" criada.'))
            else:
                self.stdout.write(self.style.WARNING(f'Natureza de Operação "{natureza.descricao}" atualizada.'))

        self.stdout.write(self.style.SUCCESS('Naturezas de Operação populadas com sucesso!'))
        self.stdout.write(self.style.SUCCESS('População de dados fiscais concluída.'))
