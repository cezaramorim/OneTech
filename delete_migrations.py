import os

files_to_delete = [
    "C:/Users/cdbg2/documents/onetech/produto/migrations/0001_initial.py",
    "C:/Users/cdbg2/documents/onetech/produto/migrations/0002_initial.py",
    "C:/Users/cdbg2/documents/onetech/produto/migrations/0003_produto_unidade_fornecedor_padrao.py",
    "C:/Users/cdbg2/documents/onetech/produto/migrations/0004_remove_produto_descricao.py",
]

for f_path in files_to_delete:
    if os.path.exists(f_path):
        os.remove(f_path)
        print(f"Removido: {f_path}")
    else:
        print(f"Arquivo não encontrado (já removido?): {f_path}")

print("Remoção de arquivos de migração concluída.")
