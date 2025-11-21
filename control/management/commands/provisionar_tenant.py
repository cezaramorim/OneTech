import json
import getpass
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
from django.db import connections, DEFAULT_DB_ALIAS
from control.models import Tenant
from control.utils import use_tenant
import MySQLdb

class Command(BaseCommand):
    help = "Cria um novo tenant (banco de dados, migrações e registro) a partir de argumentos ou de um arquivo JSON."

    def add_arguments(self, parser):
        # Argumentos originais (agora opcionais se --json-file for usado)
        parser.add_argument("--nome", required=False, help="Nome comercial do tenant")
        parser.add_argument("--slug", required=False, help="Slug para URL (e.g., 'cliente-a')")
        parser.add_argument("--dominio", required=False, help="Subdomínio de acesso (e.g., 'cliente-a.onetech.app')")
        parser.add_argument("--razao_social", required=False, help="Razão Social da empresa")
        parser.add_argument("--cnpj", required=False, help="CNPJ da empresa (formato XX.XXX.XXX/XXXX-XX)")
        
        # Novo argumento para o arquivo JSON
        parser.add_argument("--json-file", type=str, help="Caminho para um arquivo JSON com os dados do tenant.")

        # Argumentos para o superusuário inicial do tenant
        parser.add_argument("--admin-user", type=str, help="Username do usuário administrador do tenant.")
        parser.add_argument("--admin-email", type=str, help="Email do usuário administrador do tenant.")
        parser.add_argument("--admin-pass", type=str, help="Senha do usuário administrador do tenant.")

    def handle(self, *args, **opts):
        if opts['json_file']:
            self.stdout.write(self.style.SUCCESS(f"Carregando dados do arquivo JSON: {opts['json_file']}"))
            try:
                with open(opts['json_file'], 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Validação dos dados do JSON
                required_keys = ['nome', 'slug', 'dominio', 'razao_social', 'cnpj']
                if not all(key in data for key in required_keys):
                    raise CommandError("O arquivo JSON não contém todas as chaves necessárias: " + ", ".join(required_keys))
                
                opts.update(data)

            except FileNotFoundError:
                raise CommandError(f"Arquivo JSON não encontrado em: {opts['json_file']}")
            except json.JSONDecodeError:
                raise CommandError(f"Erro ao decodificar o arquivo JSON. Verifique o formato.")
        
        # Validação para garantir que temos os dados necessários de alguma fonte
        required_opts = ['nome', 'slug', 'dominio', 'razao_social', 'cnpj']
        if not all(opts.get(key) for key in required_opts):
            raise CommandError("Todos os argumentos são necessários, seja via linha de comando ou arquivo JSON (--nome, --slug, --dominio, --razao_social, --cnpj).")

        self.stdout.write(self.style.SUCCESS("Iniciando provisionamento de novo tenant..."))

        nome = opts['nome']
        slug = opts['slug']
        dominio = opts['dominio']
        razao_social = opts['razao_social']
        cnpj = opts['cnpj']

        db_name = f"onetech_{slug}"
        db_user = f"onetech_{slug}"
        db_password = "senha_forte_e_unica_a_ser_trocada"

        if Tenant.objects.filter(slug=slug).exists() or Tenant.objects.filter(db_name=db_name).exists():
            raise CommandError(f"Tenant com slug '{slug}' ou db_name '{db_name}' já existe.")

        try:
            default_db_conn = connections[DEFAULT_DB_ALIAS]
            conn = MySQLdb.connect(
                host=default_db_conn.settings_dict['HOST'],
                user=default_db_conn.settings_dict['USER'],
                passwd=default_db_conn.settings_dict['PASSWORD'],
                port=int(default_db_conn.settings_dict['PORT']),
                charset='utf8mb4' # Adicionado para suportar caracteres especiais
            )
            cursor = conn.cursor()
            
            self.stdout.write(f"Criando banco de dados `{db_name}`...")
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")

            self.stdout.write(f"Criando usuário `{db_user}` no banco de dados...")
            # Apaga o usuário se ele já existir para garantir um estado limpo
            cursor.execute(f"DROP USER IF EXISTS '{db_user}'@'localhost';")
            cursor.execute(f"CREATE USER '{db_user}'@'localhost' IDENTIFIED BY '{db_password}';")
            
            self.stdout.write(f"Concedendo privilégios para `{db_user}` no banco `{db_name}`...")
            cursor.execute(f"GRANT ALL PRIVILEGES ON `{db_name}`.* TO '{db_user}'@'localhost';")
            cursor.execute("FLUSH PRIVILEGES;")
            
            conn.commit()
            cursor.close()
            conn.close()
            self.stdout.write(self.style.SUCCESS(f"Banco de dados '{db_name}' criado."))
        except Exception as e:
            raise CommandError(f"Falha ao criar o banco de dados: {e}")

        try:
            tenant = Tenant.objects.create(
                nome=nome,
                slug=slug,
                dominio=dominio,
                razao_social=razao_social,
                cnpj=cnpj,
                db_name=db_name,
                db_user=db_user,
                db_password=db_password,
            )
            self.stdout.write(self.style.SUCCESS(f"Tenant '{tenant.nome}' registrado no banco de controle."))
        except Exception as e:
            raise CommandError(f"Falha ao registrar o tenant: {e}")

        try:
            self.stdout.write(self.style.WARNING(f"Executando migrações para o banco '{db_name}'..."))
            
            # Copia a configuração da conexão padrão para herdar todas as opções
            db_conn = connections[DEFAULT_DB_ALIAS].settings_dict.copy()
            # Sobrescreve apenas o nome do banco de dados
            db_conn['NAME'] = tenant.db_name
            # Força o charset e a collation para evitar erros de FK com tabelas InnoDB
            db_conn.setdefault('OPTIONS', {})['init_command'] = 'SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci'
            connections.settings[tenant.db_name] = db_conn
            
            # Com o router devidamente configurado, o Django pode determinar automaticamente
            # quais apps devem ser migrados para o banco de dados do tenant.
            call_command('migrate', database=tenant.db_name, interactive=False)
            self.stdout.write(self.style.SUCCESS("Migrações concluídas."))
        except Exception as e:
            raise CommandError(f"Falha ao executar migrações para '{db_name}': {e}")
        
        # Fase 4.3: Criar um superusuário para o tenant (interativo se não for fornecido)
        self.stdout.write(self.style.SUCCESS("\n--- Criação do Usuário Administrador ---"))
        
        admin_user = opts.get('admin_user')
        admin_email = opts.get('admin_email')
        admin_pass = opts.get('admin_pass')

        # Interage com o usuário se os detalhes não forem passados como argumentos
        if not (admin_user and admin_email and admin_pass):
            self.stdout.write(self.style.WARNING("Detalhes do administrador não fornecidos via argumentos. Solicitando interativamente..."))
            if not admin_user:
                while True:
                    admin_user = input("Username do Administrador: ")
                    if admin_user:
                        break
                    self.stdout.write(self.style.ERROR("O username não pode estar em branco."))
            if not admin_email:
                while True:
                    admin_email = input("Email do Administrador: ")
                    if admin_email:
                        break
                    self.stdout.write(self.style.ERROR("O email não pode estar em branco."))
            if not admin_pass:
                while True:
                    p1 = getpass.getpass("Senha do Administrador: ")
                    p2 = getpass.getpass("Confirme a Senha: ")
                    if p1 != p2:
                        self.stdout.write(self.style.ERROR("As senhas não conferem. Tente novamente."))
                    elif not p1:
                        self.stdout.write(self.style.ERROR("A senha não pode estar em branco."))
                    else:
                        admin_pass = p1
                        break
        
        self.stdout.write(self.style.WARNING(f"Criando superusuário '{admin_user}' para o tenant '{nome}'..."))
        try:
            with use_tenant(tenant):
                User = get_user_model()
                if User.objects.filter(username=admin_user).exists():
                    self.stdout.write(self.style.SUCCESS(f"Usuário '{admin_user}' já existe no tenant '{nome}'."))
                else:
                    User.objects.create_superuser(
                        username=admin_user,
                        email=admin_email,
                        password=admin_pass
                    )
                    self.stdout.write(self.style.SUCCESS(f"Superusuário '{admin_user}' criado com sucesso!"))
        except Exception as e:
            raise CommandError(f"Falha ao criar superusuário para o tenant '{nome}': {e}")

        self.stdout.write(self.style.SUCCESS(f"\nProvisionamento do tenant '{nome}' concluído!"))
        self.stdout.write(self.style.SUCCESS(f"Acesse em http://{dominio}:8000 e faça login com o usuário '{admin_user}'."))
        self.stdout.write(self.style.SUCCESS("Você pode criar usuários comuns no menu 'Configurações' > 'Novo Usuário'."))