import json
from django.core.management.base import BaseCommand
from produto.models import NCM

class Command(BaseCommand):
    help = 'Importa ou atualiza os dados NCM a partir de um arquivo JSON local oficial da Receita.'

    def handle(self, *args, **options):
        try:
            with open('produto/data/ncm.json', encoding='utf-8') as f:
                data = json.load(f)

            nomenclaturas = data.get("Nomenclaturas", [])
            count = 0

            for item in nomenclaturas:
                codigo = item.get("Codigo")
                descricao = item.get("Descricao")
                if codigo and descricao:
                    NCM.objects.update_or_create(codigo=codigo.strip(), defaults={"descricao": descricao.strip()})
                    count += 1

            self.stdout.write(self.style.SUCCESS(f"{count} códigos NCM importados/atualizados com sucesso."))

        except FileNotFoundError:
            self.stderr.write(self.style.ERROR("Arquivo ncm.json não encontrado em produto/data/."))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Erro: {str(e)}"))
