import json
import re
from functools import lru_cache
from pathlib import Path


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


def obter_nivel_ncm(value):
    codigo = normalizar_codigo_ncm(value)
    tamanho = len(codigo)

    if tamanho <= 2:
        return "Capítulo"
    if tamanho <= 4:
        return "Posição"
    if tamanho == 5:
        return "Subposição parcial"
    if tamanho == 6:
        return "Subposição"
    if tamanho == 7:
        return "Item parcial"
    if tamanho == 8:
        return "Item/Subitem"
    return "Indefinido"


def normalizar_texto_mojibake(value):
    if not isinstance(value, str):
        return value
    if any(marker in value for marker in ("Ãƒ", "Ã‚", "ï¿½")):
        try:
            return value.encode("latin1").decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            return value
    return value


@lru_cache(maxsize=1)
def carregar_metadados_ncm():
    caminho_json = Path(__file__).resolve().parent / "data" / "ncm.json"
    if not caminho_json.exists():
        return {}

    try:
        with caminho_json.open(encoding="utf-8") as arquivo:
            data = json.load(arquivo)
    except (OSError, json.JSONDecodeError):
        return {}

    nomenclaturas = data.get("Nomenclaturas") or []
    return {
        "vigencia": data.get("Data_Ultima_Atualizacao_NCM", ""),
        "ato": data.get("Ato", ""),
        "total_itens": len(nomenclaturas),
    }

