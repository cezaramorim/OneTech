# python -m tools.bootstrap_assistant (Roda na raix do projeto e cria o assistent)
# tools/bootstrap_assistant.py
from openai import OpenAI
from pathlib import Path
import tools._env  # carrega .env

client = OpenAI()
VS_ID = Path(".vector_store_id").read_text().strip()

# pega a API de assistants (GA ou beta)
assistants_api = getattr(client, "assistants", None) or getattr(getattr(client, "beta", None), "assistants", None)
if assistants_api is None:
    raise RuntimeError("Assistants API não disponível neste SDK/import.")

assistant = assistants_api.create(
    name="Onetech Assistant",
    model="gpt-4.1",                   # modelo com ferramentas
    tools=[{"type": "file_search"}],
    tool_resources={"file_search": {"vector_store_ids": [VS_ID]}}
)

Path(".assistant_id").write_text(assistant.id, encoding="utf-8")
print("Assistant criado:", assistant.id)

