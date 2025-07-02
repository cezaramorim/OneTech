from django import template
from django.contrib.humanize.templatetags.humanize import intcomma

register = template.Library()

@register.filter(name='br_currency')
def br_currency(value):
    """Formata um número como moeda brasileira (R$ 1.234,56)."""
    try:
        value = round(float(value), 2)
        # Adiciona separadores de milhar e troca a vírgula decimal por um placeholder
        formatted_value = intcomma(value).replace(",", "|").replace(".", ",").replace("|", ".")
        return f"R$ {formatted_value}"
    except (ValueError, TypeError):
        return value

@register.filter(name='replace')
def replace_filter(value, arg):
    """Substitui todas as ocorrências de uma substring por outra.
    Uso: {{ value|replace:"old_char|new_char" }}"""
    if not isinstance(value, str):
        return value
    try:
        old, new = arg.split('|', 1) # Agora divide por pipe
        return value.replace(old, new)
    except ValueError:
        # Se o argumento não estiver no formato esperado, retorna o valor original
        return value
