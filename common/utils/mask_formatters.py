import re

def format_cnpj(value):
    """Aplica a máscara de CNPJ (XX.XXX.XXX/XXXX-XX)."""
    if not value:
        return ""
    clean_value = re.sub(r'\D', '', str(value)) # Remove caracteres não numéricos
    if len(clean_value) == 14:
        return f"{clean_value[:2]}.{clean_value[2:5]}.{clean_value[5:8]}/{clean_value[8:12]}-{clean_value[12:]}"
    return value

def format_ie(value):
    """Aplica uma máscara comum para Inscrição Estadual (XXX.XXX.XXX-XXX)."""
    if not value:
        return ""
    clean_value = re.sub(r'\D', '', str(value))
    # IE pode ter tamanhos variados, esta é uma máscara comum
    if len(clean_value) == 9: # Ex: SP
        return f"{clean_value[:3]}.{clean_value[3:6]}.{clean_value[6:]}"
    elif len(clean_value) == 10: # Ex: MG
        return f"{clean_value[:3]}.{clean_value[3:6]}.{clean_value[6:9]}-{clean_value[9:]}"
    elif len(clean_value) == 11: # Ex: RJ
        return f"{clean_value[:2]}.{clean_value[2:5]}.{clean_value[5:8]}.{clean_value[8:]}"
    elif len(clean_value) == 12: # Ex: PR
        return f"{clean_value[:3]}.{clean_value[3:8]}-{clean_value[8:]}"
    elif len(clean_value) == 13: # Ex: RS
        return f"{clean_value[:3]}.{clean_value[3:9]}.{clean_value[9:]}"
    elif len(clean_value) == 14: # Ex: BA
        return f"{clean_value[:7]}-{clean_value[7:]}"
    return value # Retorna o valor original se não corresponder a nenhuma máscara

def format_im(value):
    """Retorna a Inscrição Municipal (geralmente apenas números, sem máscara padrão)."""
    if not value:
        return ""
    return re.sub(r'\D', '', str(value)) # Remove caracteres não numéricos

def format_phone(value):
    """Aplica a máscara de telefone/celular (XX) XXXX-XXXX ou (XX) XXXXX-XXXX."""
    if not value:
        return ""
    clean_value = re.sub(r'\D', '', str(value))
    if len(clean_value) == 10: # Telefone fixo com DDD
        return f"({clean_value[:2]}) {clean_value[2:6]}-{clean_value[6:]}"
    elif len(clean_value) == 11: # Celular com DDD (com 9 na frente)
        return f"({clean_value[:2]}) {clean_value[2:7]}-{clean_value[7:]}"
    return value
