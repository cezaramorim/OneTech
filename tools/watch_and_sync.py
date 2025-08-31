# python -m tools.watch_and_sync (Roda na raiz do projeto e atualiza inedexar do 
# vector store)
# tools/watch_and_sync.py
import time, json
from pathlib import Path
from fnmatch import fnmatch
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from openai import OpenAI

import tools._env  # carrega .env

ROOT = Path(".").resolve()
VS_ID_PATH = ROOT / ".vector_store_id"
if not VS_ID_PATH.exists():
    raise SystemExit("⚠️  .vector_store_id não encontrado. Rode antes: python -m tools.sync_repo")

VS_ID = VS_ID_PATH.read_text().strip()
client = OpenAI()

# Mesmos filtros do sync, ajuste se quiser
GLOBS = ["**/*.py","**/*.html","**/*.js","**/*.css","**/*.md",
         "**/*.json","**/*.sql","**/*.yml","**/*.yaml"]
EXCLUDES = [
    "**/.venv/**","**/venv/**","**/node_modules/**","**/__pycache__/**",
    "**/migrations/**","**/.git/**","**/*.env","**/dist/**","**/build/**",
    "**/static/**","**/media/**","**/*.png","**/*.jpg","**/*.jpeg","**/*.pdf","**/*.gif"
]

MAP_PATH = ROOT / ".vector_store_map.json"   # caminho->file_id no VS (ajuda a deletar certo)
if MAP_PATH.exists():
    PATH2ID = json.loads(MAP_PATH.read_text(encoding="utf-8"))
else:
    PATH2ID = {}

def include(p: Path) -> bool:
    if not p.is_file(): return False
    sp = str(p)
    if any(fnmatch(sp, pat) for pat in EXCLUDES):
        return False
    # precisa casar com ao menos 1 GLOB
    return any(fnmatch(sp, pat) for pat in GLOBS)

def save_map():
    MAP_PATH.write_text(json.dumps(PATH2ID, ensure_ascii=False, indent=2), encoding="utf-8")

def upload_file(p: Path):
    """Envia/atualiza 1 arquivo no Vector Store e guarda o id no MAP."""
    try:
        print(f"↑ Enviando: {p}")
        rsp = client.vector_stores.files.upload(
            vector_store_id=VS_ID,
            file=open(str(p), "rb")
        )
        fid = getattr(rsp, "id", None) or getattr(rsp, "file_id", None)
        if fid:
            rel = str(p.relative_to(ROOT))
            PATH2ID[rel] = fid
            save_map()
        else:
            print("⚠️  Upload feito, mas não consegui obter o id do arquivo.")
    except Exception as e:
        print("✗ Falha upload:", e)

def delete_file(p: Path):
    """Remove do Vector Store o arquivo correspondente (se soubermos o id)."""
    rel = str(p.relative_to(ROOT))
    fid = PATH2ID.get(rel)
    if fid:
        try:
            print(f"↓ Removendo do VS: {rel}")
            client.vector_stores.files.delete(vector_store_id=VS_ID, file_id=fid)
            PATH2ID.pop(rel, None)
            save_map()
        except Exception as e:
            print("✗ Falha ao remover:", e)
    else:
        # Fallback: tentar localizar por nome (menos preciso)
        try:
            print(f"… Procurando por nome para remover: {p.name}")
            items = client.vector_stores.files.list(vector_store_id=VS_ID, limit=1000)
            for f in items.data:
                name = (f.filename or "").split("/")[-1]
                if name.lower() == p.name.lower():
                    client.vector_stores.files.delete(vector_store_id=VS_ID, file_id=f.id)
                    print("↓ Removido por nome:", name)
                    break
        except Exception as e:
            print("✗ Falha no fallback de remoção:", e)

# Debounce simples para evitar uploads duplicados em salvações rápidas
LAST_SEEN = {}
DEBOUNCE_MS = 400

class Handler(FileSystemEventHandler):
    def _debounced(self, path: str) -> bool:
        now = time.time() * 1000
        last = LAST_SEEN.get(path, 0)
        if (now - last) < DEBOUNCE_MS:
            return False
        LAST_SEEN[path] = now
        return True

    def on_created(self, event):
        p = Path(event.src_path)
        if include(p) and self._debounced(event.src_path):
            upload_file(p)

    def on_modified(self, event):
        p = Path(event.src_path)
        if include(p) and self._debounced(event.src_path):
            upload_file(p)

    def on_moved(self, event):
        src = Path(event.src_path); dst = Path(event.dest_path)
        if include(src): delete_file(src)
        if include(dst) and self._debounced(event.dest_path):
            upload_file(dst)

    def on_deleted(self, event):
        p = Path(event.src_path)
        if (ROOT / p).exists():  # às vezes eventos espúrios
            return
        # só tenta deletar se seria um arquivo incluído
        if any(fnmatch(str(p), g) for g in GLOBS) and not any(fnmatch(str(p), ex) for ex in EXCLUDES):
            delete_file(p)

if __name__ == "__main__":
    print("👀 Observando alterações… (Ctrl+C para sair)")
    obs = Observer()
    obs.schedule(Handler(), str(ROOT), recursive=True)
    obs.start()
    try:
        while True: time.sleep(0.5)
    except KeyboardInterrupt:
        obs.stop()
    obs.join()
