from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Valida baseline de seguranca (OWASP basico) via configuracoes do projeto.'

    def handle(self, *args, **options):
        use_https = bool(getattr(settings, 'USE_HTTPS', False))

        checks = [
            ('SESSION_COOKIE_HTTPONLY', bool(getattr(settings, 'SESSION_COOKIE_HTTPONLY', False))),
            (
                'SESSION_COOKIE_SECURE',
                bool(getattr(settings, 'SESSION_COOKIE_SECURE', False)) if use_https else True,
            ),
            (
                'CSRF_COOKIE_SECURE',
                bool(getattr(settings, 'CSRF_COOKIE_SECURE', False)) if use_https else True,
            ),
            ('SESSION_COOKIE_SAMESITE', str(getattr(settings, 'SESSION_COOKIE_SAMESITE', '')) in ('Lax', 'Strict')),
            ('CSRF_COOKIE_SAMESITE', str(getattr(settings, 'CSRF_COOKIE_SAMESITE', '')) in ('Lax', 'Strict')),
            ('SECURE_CONTENT_TYPE_NOSNIFF', bool(getattr(settings, 'SECURE_CONTENT_TYPE_NOSNIFF', False))),
            ('X_FRAME_OPTIONS', str(getattr(settings, 'X_FRAME_OPTIONS', '')) in ('DENY', 'SAMEORIGIN')),
            ('REST_EXCEPTION_HANDLER', getattr(settings, 'REST_FRAMEWORK', {}).get('EXCEPTION_HANDLER') == 'common.api.exception_handler.onetech_exception_handler'),
        ]

        if use_https:
            checks.extend([
                ('SECURE_SSL_REDIRECT', bool(getattr(settings, 'SECURE_SSL_REDIRECT', False))),
                ('SECURE_HSTS_SECONDS', int(getattr(settings, 'SECURE_HSTS_SECONDS', 0)) >= 31536000),
                ('SECURE_HSTS_INCLUDE_SUBDOMAINS', bool(getattr(settings, 'SECURE_HSTS_INCLUDE_SUBDOMAINS', False))),
                ('SECURE_HSTS_PRELOAD', bool(getattr(settings, 'SECURE_HSTS_PRELOAD', False))),
            ])

        failed = [name for name, ok in checks if not ok]

        self.stdout.write(f'[INFO] USE_HTTPS={use_https}')
        for name, ok in checks:
            marker = 'OK' if ok else 'FAIL'
            self.stdout.write(f'[{marker}] {name}')

        if failed:
            self.stdout.write(self.style.ERROR('Baseline de seguranca reprovada.'))
            self.stdout.write(self.style.ERROR('Falhas: ' + ', '.join(failed)))
            raise SystemExit(1)

        self.stdout.write(self.style.SUCCESS('Baseline de seguranca aprovada.'))