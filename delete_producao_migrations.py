import os

files_to_delete = [
    "C:/Users/cdbg2/documents/onetech/producao/migrations/0001_initial.py",
    "C:/Users/cdbg2/documents/onetech/producao/migrations/0002_malha_tipotela_unidade_tanque_altura_and_more.py",
    "C:/Users/cdbg2/documents/onetech/producao/migrations/0003_remove_tanque_altura_remove_tanque_atividade.py",
    "C:/Users/cdbg2/documents/onetech/producao/migrations/0004_curvacrescimentodetalhe_intervalo_trato_horas.py",
    "C:/Users/cdbg2/documents/onetech/producao/migrations/0005_curvacrescimento_peso_pretendido_and_more.py",
    "C:/Users/cdbg2/documents/onetech/producao/migrations/0006_remove_curvacrescimentodetalhe_intervalo_trato_horas_and_more.py",
    "C:/Users/cdbg2/documents/onetech/producao/migrations/0007_alter_tanque_options_remove_tanque_tipo_tela_and_more.py",
    "C:/Users/cdbg2/documents/onetech/producao/migrations/0008_alter_eventomanejo_tipo_movimento.py",
    "C:/Users/cdbg2/documents/onetech/producao/migrations/0009_tanque_tipo_tela.py",
    "C:/Users/cdbg2/documents/onetech/producao/migrations/0010_lotediario_arracoamentosugerido_and_more.py",
    "C:/Users/cdbg2/documents/onetech/producao/migrations/0011_auto_20250911_2120.py",
    "C:/Users/cdbg2/documents/onetech/producao/migrations/0012_alter_lotediario_options_and_more.py",
    "C:/Users/cdbg2/documents/onetech/producao/migrations/0013_delete_racaoperfil.py",
    "C:/Users/cdbg2/documents/onetech/producao/migrations/0014_lotediario_biomassa_inicial_and_more.py",
    "C:/Users/cdbg2/documents/onetech/producao/migrations/0015_alter_lotediario_gpd_projetado_and_more.py",
    "C:/Users/cdbg2/documents/onetech/producao/migrations/0016_alter_arracoamentorealizado_data_edicao_and_more.py",
    "C:/Users/cdbg2/documents/onetech/producao/migrations/0017_alter_curvacrescimento_peso_pretendido_and_more.py",
    "C:/Users/cdbg2/documents/onetech/producao/migrations/0018_alter_lotediario_biomassa_projetada_and_more.py",
]

for f_path in files_to_delete:
    if os.path.exists(f_path):
        os.remove(f_path)
        print(f"Removido: {f_path}")
    else:
        print(f"Arquivo não encontrado (já removido?): {f_path}")

print("Remoção de arquivos de migração de producao concluída.")
