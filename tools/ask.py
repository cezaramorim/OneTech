# python -m tools.ask "Liste endpoints 404 e arquivos afetados"
# python -m tools.ask "Ache duplicações de CSS e onde centralizar"
# python -m tools.ask "Explique por que o tema escuro não aplica no <main>"


# tools/ask.py
from openai import OpenAI
from pathlib import Path
import sys, time
import warnings

import tools._env  # carrega .env

# (opcional) ocultar avisos de depreciação
warnings.filterwarnings("ignore", category=DeprecationWarning)

client = OpenAI()

assistant_id = Path(".assistant_id").read_text().strip()
question = "Mapeie NoReverseMatch e indique views/templates."
if len(sys.argv) > 1:
    question = " ".join(sys.argv[1:])

# pega APIs (GA ou beta)
threads_api = getattr(client, "threads", None) or getattr(getattr(client, "beta", None), "threads", None)
if threads_api is None:
    raise RuntimeError("Threads API não disponível neste SDK/import.")

# cria thread com sua pergunta
thread = threads_api.create(messages=[{"role": "user", "content": question}])

# executa o assistant
run = threads_api.runs.create(thread_id=thread.id, assistant_id=assistant_id)

# espera finalizar (e trata estados)
while True:
    run = threads_api.runs.retrieve(thread_id=thread.id, run_id=run.id)
    if run.status in ("completed", "failed", "cancelled"):
        break
    if run.status == "requires_action":
        # se no futuro você tiver ferramentas que exigem ação humana, tratar aqui
        print("Execução requer ação adicional (tools).")
        break
    time.sleep(0.5)

if run.status != "completed":
    print(f"Status final: {run.status}")
    sys.exit(0)

# função para extrair texto de qualquer formato (objeto ou dict)
def get_texts_from_message(msg):
    texts = []
    content_list = getattr(msg, "content", None)
    if not content_list and isinstance(msg, dict):
        content_list = msg.get("content", [])
    if not content_list:
        return texts

    for item in content_list:
        # item pode ser objeto pydantic ou dict
        item_type = getattr(item, "type", None) or (isinstance(item, dict) and item.get("type"))
        if item_type == "text":
            txt_obj = getattr(item, "text", None) or (isinstance(item, dict) and item.get("text"))
            if txt_obj:
                val = getattr(txt_obj, "value", None) or (isinstance(txt_obj, dict) and txt_obj.get("value"))
                if val:
                    texts.append(val)
    return texts

# lê e imprime respostas do assistant
msgs = threads_api.messages.list(thread_id=thread.id)
printed = False
for m in reversed(msgs.data):
    role = getattr(m, "role", None) or (isinstance(m, dict) and m.get("role"))
    if role == "assistant":
        for t in get_texts_from_message(m):
            print(t)
            printed = True

if not printed:
    print("(Sem conteúdo textual para imprimir — verifique se a resposta contém apenas anexos ou tool_outputs.)")
