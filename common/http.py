# common/http.py
from django.http import JsonResponse

def json_ok(**payload):
    """Cria uma resposta JSON padronizada para sucesso."""
    return JsonResponse({"success": True, **payload})

def json_error(message="Ocorreu um erro.", status=400, **extra):
    """Cria uma resposta JSON padronizada para erros."""
    return JsonResponse({"success": False, "message": message, **extra}, status=status)
