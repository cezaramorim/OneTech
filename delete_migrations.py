
import os
import glob

app_dirs = [
    'C:/Users/cdbg2/documents/onetech/produto/migrations/',
    'C:/Users/cdbg2/documents/onetech/nota_fiscal/migrations/',
    'C:/Users/cdbg2/documents/onetech/accounts/migrations/',
    'C:/Users/cdbg2/documents/onetech/empresas/migrations/',
    'C:/Users/cdbg2/documents/onetech/fiscal/migrations/',
    'C:/Users/cdbg2/documents/onetech/painel/migrations/',
    'C:/Users/cdbg2/documents/onetech/relatorios/migrations/',
]

for app_dir in app_dirs:
    for f in glob.glob(os.path.join(app_dir, '[0-9][0-9][0-9][0-9]_*.py')):
        try:
            os.remove(f)
            print(f"Deleted: {f}")
        except OSError as e:
            print(f"Error deleting {f}: {e}")
