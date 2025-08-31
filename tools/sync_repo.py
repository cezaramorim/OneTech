#python -m tools.sync_repo (Roda o arquivo na raiz)
# tools/sync_repo.py
from pathlib import Path
from openai import OpenAI
from fnmatch import fnmatch
import shutil, tempfile

import tools._env  # carrega .env

client = OpenAI()

# 1) cria o vector store
vs = client.vector_stores.create(name="Onetech Repo")
print("Vector Store:", vs.id)

# 2) filtros
GLOBS = ["**/*.py","**/*.html","**/*.js","**/*.css","**/*.md",
         "**/*.json","**/*.sql","**/*.yml","**/*.yaml","**/*.txt"]
EXCLUDES = [
    "**/.venv/**","**/venv/**","**/node_modules/**","**/__pycache__/**",
    "**/migrations/**","**/.git/**","**/*.env","**/dist/**","**/build/**",
    "**/static/**","**/media/**","**/*.png","**/*.jpg","**/*.jpeg","**/*.pdf","**/*.gif",
]

# extensões permitidas pela API (minúsculas)
ALLOWED = {
    ".c",".cpp",".css",".csv",".doc",".docx",".gif",".go",".html",".java",
    ".jpeg",".jpg",".js",".json",".md",".pdf",".php",".pkl",".png",".pptx",
    ".py",".rb",".tar",".tex",".ts",".txt",".webp",".xlsx",".xml",".zip"
}

def excluded(p: Path) -> bool:
    sp = str(p)
    return any(fnmatch(sp, pat) for pat in EXCLUDES)

def matches_globs(p: Path) -> bool:
    sp = str(p)
    return any(fnmatch(sp, pat) for pat in GLOBS)

# 3) coleta
root = Path(".").resolve()
all_candidates = [p for p in root.rglob("*") if p.is_file() and matches_globs(p) and not excluded(p)]
non_empty = [p for p in all_candidates if p.stat().st_size > 0]
empty = [p for p in all_candidates if p.stat().st_size == 0]

print(f"Arquivos candidatos: {len(all_candidates)}")
print(f"Ignorando vazios (0B): {len(empty)}")
for p in empty[:10]:
    print("0B:", p)

# 4) normalização de extensão (cópia temporária se necessário)
tmpdir = Path(tempfile.mkdtemp(prefix="vs_upload_"))
upload_paths = []
skipped = 0
for p in non_empty:
    suf_lower = p.suffix.lower()
    if suf_lower not in ALLOWED:
        skipped += 1
        # comente a próxima linha se quiser ver quais
        # print("SKIP (ext não permitida):", p)
        continue

    if p.suffix == suf_lower:
        upload_paths.append(p)  # ok, já minúsculo
    else:
        # cria uma cópia com a extensão minúscula (ex.: .MD -> .md)
        rel = p.relative_to(root)
        tmp_target = tmpdir / rel
        tmp_target = tmp_target.with_suffix(suf_lower)
        tmp_target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, tmp_target)
        upload_paths.append(tmp_target)

print(f"Ignorados por extensão: {skipped}")
print("Arquivos para indexar:", len(upload_paths))

if not upload_paths:
    raise SystemExit("Nada para enviar ao Vector Store.")

# 5) envio em lotes
CHUNK = 200

def upload_batch(vs_id: str, paths):
    fobjs = [open(str(p), "rb") for p in paths]
    try:
        batch = client.vector_stores.file_batches.upload_and_poll(
            vector_store_id=vs_id,
            files=fobjs
        )
        print("Batch status:", batch.status, f"(itens: {len(paths)})")
    finally:
        for f in fobjs:
            try: f.close()
            except: pass

for i in range(0, len(upload_paths), CHUNK):
    upload_batch(vs.id, upload_paths[i:i+CHUNK])

# 6) salva o id do VS
Path(".vector_store_id").write_text(vs.id, encoding="utf-8")
print("OK. ID salvo em .vector_store_id")
print(f"Temp usado: {tmpdir}")
