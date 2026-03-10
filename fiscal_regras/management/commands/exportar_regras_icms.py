import json

from django.core.management.base import BaseCommand, CommandError

from fiscal_regras.models import RegraAliquotaICMS


class Command(BaseCommand):
    help = 'Exporta regras ICMS para um arquivo JSON.'

    def add_arguments(self, parser):
        parser.add_argument('--file', required=True, help='Caminho do arquivo de saida JSON.')

    def handle(self, *args, **options):
        path = options['file']
        dados = list(
            RegraAliquotaICMS.objects.values(
                'ativo', 'descricao', 'ncm_prefixo', 'tipo_operacao', 'modalidade',
                'uf_origem', 'uf_destino', 'origem_mercadoria', 'cst_icms_id', 'csosn_icms_id',
                'aliquota_icms', 'fcp', 'reducao_base_icms', 'prioridade',
                'vigencia_inicio', 'vigencia_fim', 'observacoes',
            )
        )

        try:
            with open(path, 'w', encoding='utf-8') as fp:
                json.dump(dados, fp, ensure_ascii=False, default=str, indent=2)
        except Exception as exc:
            raise CommandError(f'Nao foi possivel escrever arquivo: {exc}')

        self.stdout.write(self.style.SUCCESS(f'Exportacao concluida. Total: {len(dados)} regra(s).'))
