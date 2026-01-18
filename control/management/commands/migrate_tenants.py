from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
from django.db import connections, DEFAULT_DB_ALIAS
from control.models import Tenant

class Command(BaseCommand):
    help = "Executa migrações para um ou mais tenants específicos, ou para todos."

    def add_arguments(self, parser):
        parser.add_argument(
            '--tenants',
            nargs='+',
            type=str,
            help='Especifique um ou mais slugs de tenants para migrar.',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Executa migrações para todos os tenants cadastrados.',
        )
        parser.add_argument(
            '--fake',
            action='store_true',
            help='Marca as migrações como aplicadas sem de fato executá-las.',
        )

    def handle(self, *args, **options):
        tenants_to_migrate = []
        is_fake = options['fake']
        if options['all']:
            self.stdout.write(self.style.SUCCESS("Selecionando todos os tenants..."))
            tenants_to_migrate = Tenant.objects.all()
            if not tenants_to_migrate:
                self.stdout.write(self.style.WARNING("Nenhum tenant encontrado."))
                return
        elif options['tenants']:
            slugs = options['tenants']
            self.stdout.write(self.style.SUCCESS(f"Selecionando tenants: {', '.join(slugs)}"))
            tenants_to_migrate = Tenant.objects.filter(slug__in=slugs)
            
            found_slugs = {t.slug for t in tenants_to_migrate}
            missing_slugs = set(slugs) - found_slugs
            if missing_slugs:
                raise CommandError(f"Os seguintes tenants não foram encontrados: {', '.join(missing_slugs)}")
        else:
            raise CommandError("Você deve especificar quais tenants migrar usando --tenants <slug1> <slug2> ou usar a flag --all.")

        for tenant in tenants_to_migrate:
            self.stdout.write("-" * 40)
            self.stdout.write(self.style.SUCCESS(f"Processando tenant: {tenant.nome} ({tenant.slug})"))
            
            db_name = tenant.db_name
            
            try:
                # Adiciona dinamicamente a configuração do banco de dados do tenant
                db_conn_settings = connections[DEFAULT_DB_ALIAS].settings_dict.copy()
                db_conn_settings['NAME'] = db_name
                connections.settings[db_name] = db_conn_settings

                self.stdout.write(self.style.WARNING(f"Executando migrações para o banco de dados '{db_name}'..."))
                
                # Chama o comando migrate para o banco de dados do tenant
                call_command('migrate', database=db_name, interactive=False, fake=is_fake)
                
                self.stdout.write(self.style.SUCCESS(f"Migrações para '{db_name}' concluídas com sucesso."))

            except Exception as e:
                self.stderr.write(self.style.ERROR(f"Ocorreu um erro ao migrar o tenant {tenant.slug}: {e}"))
            finally:
                # Remove a configuração de conexão para não interferir com outros comandos
                if db_name in connections.settings:
                    del connections.settings[db_name]
        
        self.stdout.write("-" * 40)
        self.stdout.write(self.style.SUCCESS("Processo de migração de tenants finalizado."))
