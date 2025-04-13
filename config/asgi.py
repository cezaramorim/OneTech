"""
ASGI config for the OneTech project.

This file exposes the ASGI callable as a module-level variable named ``application``.

ASGI (Asynchronous Server Gateway Interface) é usado para aplicações assíncronas com suporte a WebSockets e outras features modernas.

Mais informações:
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

import os
from django.core.asgi import get_asgi_application

# Define o módulo de configurações padrão para o Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Obtém a aplicação ASGI para servir o projeto
application = get_asgi_application()

