import os

files_to_delete = [
    "C:/Users/cdbg2/documents/onetech/nota_fiscal/migrations/0001_initial.py",
    "C:/Users/cdbg2/documents/onetech/nota_fiscal/migrations/0002_initial.py",
    "C:/Users/cdbg2/documents/onetech/nota_fiscal/migrations/0003_notafiscal_emitente_proprio_and_more.py",
]

for f_path in files_to_delete:
    if os.path.exists(f_path):
        os.remove(f_path)
        print(f"Removido: {f_path}")
    else:
        print(f"Arquivo não encontrado (já removido?): {f_path}")

print("Remoção de arquivos de migração de nota_fiscal concluída.")
