from decouple import Config, RepositoryEnv
from pathlib import Path
import pymysql
from .connection import get_db_settings

# =======================
# Diretório Base e .env
# =======================
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = Path(__file__).resolve().parent / ".env"
config = Config(repository=RepositoryEnv(ENV_FILE))

# =======================
# Substituto do MySQLdb
# =======================
pymysql.install_as_MySQLdb()

# =======================
# Segurança e Execução
# =======================
SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', cast=bool)  # ⛔ Altere para False em produção
ALLOWED_HOSTS = config('ALLOWED_HOSTS', cast=lambda v: [s.strip() for s in v.split(',')])
#ALLOWED_HOSTS = []  # 🛡️ Ex: ['onetech.com', '127.0.0.1']

# =======================
# Banco de Dados (MySQL)
# =======================
DATABASES = {
    'default': get_db_settings()
}

# =======================
# Aplicações do Projeto
# =======================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_extensions',

    # Apps do projeto
    'rest_framework',
    'django_filters',
    'painel',
    'accounts',
    'empresas',
    'widget_tweaks',
    'produto',
    'nota_fiscal',
    'relatorios',
    'fiscal',
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    # opcional: paginação
    'DEFAULT_PAGINATION_CLASS':
        'rest_framework.pagination.LimitOffsetPagination',
    'PAGE_SIZE': 25,
    
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],    
}

# =======================
# Middleware
# =======================
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
]

# =======================
# Rotas e WSGI
# =======================
ROOT_URLCONF = 'config.urls'
WSGI_APPLICATION = 'config.wsgi.application'

# =======================
# Templates
# =======================
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],  # Diretório global de templates
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'painel.context_processors.definir_data_tela',
            ],
        },
    },
]

# =======================
# Validação de Senhas
# =======================
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# =======================
# Internacionalização
# =======================
LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# =======================
# Arquivos Estáticos
# =======================
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']

# =======================
# Modelo de Usuário Customizado
# =======================
AUTH_USER_MODEL = 'accounts.User'

# =======================
# Chave primária padrão
# =======================
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# =======================
# Redirecionamentos de Login/Logout
# =======================
LOGIN_URL = '/accounts/login/'          # Redireciona para o login se não autenticado
LOGIN_REDIRECT_URL = '/'                # Após login bem-sucedido, vai para a home
LOGOUT_REDIRECT_URL = '/accounts/login/'  # Após logout, volta para a tela de login

# =======================
# Sessão - Expiração e Segurança
# =======================
SESSION_EXPIRE_AT_BROWSER_CLOSE = True      # Expira ao fechar o navegador
SESSION_COOKIE_AGE = 300                    # Expira após 5 minutos (300 segundos) de inatividade
SESSION_SAVE_EVERY_REQUEST = True           # Renova a sessão a cada requisição ativa

# =======================
# Internacionalização de Traduções (i18n)
# =======================
LOCALE_PATHS = [
    BASE_DIR / 'locale',  # onde os arquivos .po e .mo ficarão salvos
]
