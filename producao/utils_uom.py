from decimal import Decimal, ROUND_HALF_UP

# --- Constantes de Quantização ---
Q3 = Decimal("0.001") # Para kg
Q2 = Decimal("0.01")  # Para FCR
KG_POR_G = Decimal('0.001')

# --- Helper Interno de Conversão Segura ---

def _to_dec(x) -> Decimal:
    """Converte um valor para Decimal de forma segura, evitando imprecisão de float."""
    if x is None:
        return Decimal('0')
    if isinstance(x, Decimal):
        return x
    # A conversão para string é a chave para evitar a representação binária imprecisa do float.
    return Decimal(str(x))

# --- Funções de Arredondamento ---

def q3(x) -> Decimal:
    """Quantiza um valor para 3 casas decimais (padrão kg)."""
    return _to_dec(x).quantize(Q3, rounding=ROUND_HALF_UP)

def q2(x) -> Decimal:
    """Quantiza um valor para 2 casas decimais (padrão FCR)."""
    return _to_dec(x).quantize(Q2, rounding=ROUND_HALF_UP)

# --- Funções de Conversão de Unidade ---

def g_to_kg(gramas) -> Decimal:
    """Converte um valor de gramas para quilogramas."""
    return q3(_to_dec(gramas) * KG_POR_G)

def kg_to_g(quilogramas) -> Decimal:
    """Converte um valor de quilogramas para gramas."""
    # O resultado em gramas pode ter casas decimais, mas não precisa da precisão de 3 casas do kg.
    return (_to_dec(quilogramas) / KG_POR_G).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)

# --- Funções de Cálculo de Negócio ---

def calc_biomassa_kg(quantidade_peixes, peso_medio_g) -> Decimal:
    """
    Calcula a biomassa total em kg.
    O resultado é quantizado para 3 casas decimais.
    """
    qtd = _to_dec(quantidade_peixes)
    peso = _to_dec(peso_medio_g)
    biomassa_g = qtd * peso
    return g_to_kg(biomassa_g)

def calc_racao_kg(biomassa_kg, pct_bw_dia) -> Decimal:
    """
    Calcula a quantidade de ração sugerida em kg.
    O resultado é quantizado para 3 casas decimais.
    """
    biomassa = _to_dec(biomassa_kg)
    fator_bw = _to_dec(pct_bw_dia) / Decimal('100')
    racao = biomassa * fator_bw
    return q3(racao)

def calc_fcr(kg_racao, kg_ganho_biomassa) -> Decimal:
    """
    Calcula o Fator de Conversão Alimentar (FCR).
    O resultado é quantizado para 2 casas decimais.
    """
    racao = _to_dec(kg_racao)
    ganho = _to_dec(kg_ganho_biomassa)

    if ganho.is_zero():
        return Decimal('0.00')
    
    fcr = racao / ganho
    return q2(fcr)