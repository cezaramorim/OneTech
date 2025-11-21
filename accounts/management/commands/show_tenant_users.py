from django.core.management.base import BaseCommand, CommandError
from control.models import Tenant
from control.utils import use_tenant
from accounts.models import User

class Command(BaseCommand):
    help = "Lista os usuários de um tenant específico. Demonstra o uso do context manager 'use_tenant'."

    def add_arguments(self, parser):
        parser.add_argument("--tenant-slug", required=True, type=str, help="O slug do tenant a ser inspecionado.")

    def handle(self, *args, **options):
        tenant_slug = options['tenant_slug']
        self.stdout.write(self.style.SUCCESS(f"Buscando tenant com slug: '{tenant_slug}'..."))

        try:
            # Busca o tenant no banco de dados 'default'
            tenant = Tenant.objects.using('default').get(slug=tenant_slug)
        except Tenant.DoesNotExist:
            raise CommandError(f"Tenant com slug '{tenant_slug}' não encontrado no banco de dados de controle.")

        self.stdout.write(self.style.SUCCESS(f"Ativando contexto para o tenant '{tenant.nome}' (Banco: {tenant.db_name})..."))

        # Aqui está a mágica: usamos o context manager para garantir que
        # todas as queries dentro deste bloco sejam roteadas para o banco do tenant.
        with use_tenant(tenant):
            # Esta query será executada no banco de dados do tenant por causa do router
            # que agora consegue obter o tenant correto através do get_current_tenant().
            users = User.objects.all()
            
            self.stdout.write(self.style.WARNING(f"Usuários encontrados no banco de dados '{tenant.db_name}':"))
            
            if users.exists():
                for user in users:
                    self.stdout.write(f"  - ID: {user.id}, Username: {user.username}, Nome: {user.nome_completo or 'N/A'}")
            else:
                # Para a demonstração, vamos criar um usuário se não houver nenhum.
                self.stdout.write("  Nenhum usuário encontrado. Criando um usuário de exemplo 'admin_tenant'...")
                User.objects.create_superuser(
                    username='admin_tenant', 
                    email='admin@tenant.com', 
                    password='admin', 
                    nome_completo='Admin do Tenant'
                )
                self.stdout.write(self.style.SUCCESS("  Usuário 'admin_tenant' criado com sucesso."))
                self.stdout.write(self.style.WARNING("  Execute o comando novamente para ver o usuário listado."))

        
        self.stdout.write(self.style.SUCCESS("Comando concluído."))
