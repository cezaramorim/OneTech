from django import template
from common.utils.mask_formatters import format_cnpj, format_ie, format_im, format_phone

register = template.Library()

@register.filter
def mask_cnpj(value):
    return format_cnpj(value)

@register.filter
def mask_ie(value):
    return format_ie(value)

@register.filter
def mask_im(value):
    return format_im(value)

@register.filter
def mask_phone(value):
    return format_phone(value)
