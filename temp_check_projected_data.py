from producao.models import Lote, LoteDiario
from django.db.models import Max

# 1. Encontrar o lote mais recente (ou um lote específico que você criou para teste)
lote_teste = Lote.objects.latest('data_povoamento') # Pega o lote mais recentemente povoado

print(f"\n--- Dados Projetados para o Lote: {lote_teste.nome} (ID: {lote_teste.id}) ---")

# 2. Buscar todos os registros LoteDiario projetados para este lote
registros_projetados = LoteDiario.objects.filter(lote=lote_teste).order_by('data_evento')

if not registros_projetados.exists():
    print("Nenhum registro LoteDiario projetado encontrado para este lote.")
else:
    print(f"Total de registros projetados: {registros_projetados.count()}\n")
    print("Data        | Qtd. Proj. | Peso Médio Proj. | Ração Sugerida (kg)")
    print("------------------------------------------------------------------")
    for r in registros_projetados:
        # Formata a saída para melhor visualização
        data_str = r.data_evento.strftime('%Y-%m-%d')
        qtd_proj = f"{r.quantidade_projetada:.2f}" if r.quantidade_projetada is not None else "N/A"
        peso_proj = f"{r.peso_medio_projetado:.2f}" if r.peso_medio_projetado is not None else "N/A"
        racao_sug = f"{r.racao_sugerida_kg:.2f}" if r.racao_sugerida_kg is not None else "N/A"
        
        print(f"{data_str} | {qtd_proj.ljust(11)} | {peso_proj.ljust(16)} | {racao_sug.ljust(19)}")
    print("------------------------------------------------------------------")
