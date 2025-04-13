"""
WSGI config for the OneTech project.

This file exposes the WSGI callable as a module-level variable named ``application``.

It's used by Django’s built-in servers and deployment tools (e.g., Gunicorn, uWSGI).

See: https://docs.djangoproject.com/en/5.1/howto/deployment/wsgi/
"""

import os
from django.core.wsgi import get_wsgi_application

# Define o módulo de configurações padrão do projeto
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Aponta o WSGI callable para o servidor usar
application = get_wsgi_application()
