# tools/ask_responses.py
from openai import OpenAI
from pathlib import Path
import sys

import tools._env  # carrega o .env

client = OpenAI()

# 1) ler o id do Vector Store (criado pelo sync_repo)
VS_ID = Path(".vector_store_id").read_text().strip()

# 2) pegar a pergunta (ou usar uma default)
question = "Mapeie NoReverseMatch e indique views/templates."
if len(sys.argv) > 1:
    question = " ".join(sys.argv[1:])

# 3) chamar a Responses API com a ferramenta file_search
resp = client.responses.create(
    model="gpt-4.1",               # pode usar gpt-4o-mini para baratear
    input=question,
    tools=[{
        "type": "file_search",
        "vector_store_ids": [VS_ID]
    }],
)

# 4) imprimir texto da resposta (robusto)
printed = False
txt = getattr(resp, "output_text", None)
if txt:
    print(txt)
    printed = True

if not printed:
    for out in getattr(resp, "output", []) or []:
        for c in getattr(out, "content", []) or []:
            t = getattr(c, "text", None)
            if t:
                val = getattr(t, "value", None) or getattr(t, "text", None)
                if val:
                    print(val)
                    printed = True

if not printed:
    print("(Sem conteúdo textual — possivelmente apenas anexos/annotations.)")

# 5) (Opcional) listar arquivos do Vector Store citados como contexto
ann = []
for out in getattr(resp, "output", []) or []:
    for c in getattr(out, "content", []) or []:
        t = getattr(c, "text", None)
        if t and getattr(t, "annotations", None):
            for a in t.annotations:
                fname = getattr(a, "filename", None) or getattr(a, "file_name", None)
                if fname:
                    ann.append(fname)

if ann:
    print("\n[Arquivos usados como contexto]")
    for f in sorted(set(ann)):
        print(" -", f)
