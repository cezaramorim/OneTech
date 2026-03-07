import re


def normalizar_codigo_ncm(value):
    if value in (None, ''):
        return ''
    digits = re.sub(r'\D', '', str(value))
    return digits[:8]


def formatar_codigo_ncm(value):
    codigo = normalizar_codigo_ncm(value)
    if len(codigo) == 8:
        return f"{codigo[:4]}.{codigo[4:6]}.{codigo[6:]}"
    if len(codigo) == 7:
        return f"{codigo[:4]}.{codigo[4:6]}.{codigo[6:]}"
    if len(codigo) == 6:
        return f"{codigo[:4]}.{codigo[4:]}"
    return codigo


def normalizar_texto_mojibake(value):
    if not isinstance(value, str):
        return value
    if any(marker in value for marker in ("Ã", "Â", "�")):
        try:
            return value.encode("latin1").decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            return value
    return value
