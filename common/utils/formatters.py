from datetime import datetime
from decimal import Decimal, InvalidOperation

# ✅ Conversão segura de valores numéricos no padrão BR para Decimal
def converter_valor_br(valor):
    """
    Converte string '1.234,56' ou float para Decimal.
    """
    if not valor:
        return Decimal("0.0")
    try:
        valor_str = str(valor).replace(".", "").replace(",", ".")
        v = Decimal(valor_str.strip())
        if v > Decimal('99999999.9999999999'):
            return Decimal('99999999.9999999999')
        return v
    except InvalidOperation:
        return Decimal("0.0")

# ✅ Conversão segura de string para data
def converter_data_para_date(data_str):
    """
    Converte data em formato BR (dd/mm/yyyy) ou ISO (yyyy-mm-dd) para objeto date.
    """
    if not data_str:
        return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(data_str, fmt).date()
        except Exception:
            continue
    return None

# ✅ Formatação para exibição em relatórios/templates
def formatar_data_iso_para_br(data_iso):
    """Converte '2023-08-26T07:55:00-03:00' ou '2023-08-26' para '26/08/2023'."""
    if not data_iso:
        return ""
    try:
        if "T" in data_iso:
            if data_iso.endswith("-03:00"):
                data_iso = data_iso[:-6]
            dt = datetime.strptime(data_iso, "%Y-%m-%dT%H:%M:%S")
        else:
            dt = datetime.strptime(data_iso, "%Y-%m-%d")
        return dt.strftime("%d/%m/%Y")
    except Exception:
        return data_iso

def formatar_numero_br(valor):
    """Formata número para padrão brasileiro: 1.234,56"""
    try:
        return f"{float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return valor

def formatar_moeda_br(valor):
    """Formata moeda para padrão brasileiro: R$ 1.234,56"""
    try:
        return f"R$ {float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return valor

def formatar_dados_para_br(dados):
    """Aplica formatação pt-BR em um dicionário inteiro."""
    if isinstance(dados, dict):
        return {k: formatar_dados_para_br(v) for k, v in dados.items()}
    elif isinstance(dados, list):
        return [formatar_dados_para_br(v) for v in dados]
    elif isinstance(dados, (int, float, Decimal)):
        return formatar_numero_br(dados)
    elif isinstance(dados, str):
        if "-" in dados and len(dados) >= 10:
            return formatar_data_iso_para_br(dados)
        return dados
    return dados
