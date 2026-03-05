# -*- coding: utf-8 -*-
import json
import logging
from datetime import datetime
from decimal import Decimal

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required, permission_required

from .models import FaseProducao, ParametroAmbientalDiario, Tanque

logger = logging.getLogger(__name__)


def _to_decimal_or_none(v):
    """Converte para Decimal, aceitando '', None e strings com vírgula."""
    if v is None:
        return None
    if isinstance(v, str):
        v = v.strip()
        if v == "":
            return None
        v = v.replace(",", ".")
    try:
        return Decimal(str(v))
    except Exception:
        return None


@login_required
@require_http_methods(["GET"])
@permission_required('producao.view_faseproducao', raise_exception=True)
def api_fases_com_tanques(request):
    """
    Retorna todas as fases de produção com seus respectivos tanques
    """
    try:
        fases = FaseProducao.objects.filter(ativa=True).order_by('nome')
        fases_data = []
        for fase in fases:
            tanques = Tanque.objects.filter(
                fase_producao_atual=fase,
                ativo=True
            ).values_list('nome', flat=True)
            fases_data.append({
                'id': fase.id,
                'nome': fase.nome,
                'tanques': list(tanques) if tanques else []
            })
        return JsonResponse({
            'success': True,
            'fases': fases_data
        })
    except Exception as e:
        logger.exception(f"Erro ao buscar fases com tanques: {e}")
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
@permission_required('producao.change_parametroambientaldiario', raise_exception=True)
def api_ambiente_upsert(request):
    """
    UPSERT (cria/atualiza) parâmetros ambientais diários por FASE e DATA.
    Aceita até 5 leituras (um por trato): od_1..od_5 e temp_1..temp_5.
    Também aceita parâmetros químicos: ph, amonia, nitrito, nitrato, alcalinidade.
    O model calcula automaticamente: od_medio, temp_media, temp_min, temp_max, variacao_termica.
    """
    try:
        payload = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'JSON inválido.'}, status=400)

    fase_id = payload.get("fase_id")
    data_str = payload.get("data")

    if not fase_id:
        return JsonResponse({'success': False, 'message': 'fase_id é obrigatório.'}, status=400)
    if not data_str:
        return JsonResponse({'success': False, 'message': 'data é obrigatória (AAAA-MM-DD).'}, status=400)

    try:
        data_alvo = datetime.strptime(data_str, "%Y-%m-%d").date()
    except ValueError:
        return JsonResponse({'success': False, 'message': 'Formato de data inválido. Use AAAA-MM-DD.'}, status=400)

    fase = FaseProducao.objects.filter(pk=fase_id).first()
    if not fase:
        return JsonResponse({'success': False, 'message': f'FaseProducao {fase_id} não encontrada.'}, status=404)

    # Monta campos permitidos (até 5 leituras)
    campos_leitura = {}
    for i in range(1, 6):
        campos_leitura[f"od_{i}"] = _to_decimal_or_none(payload.get(f"od_{i}"))
        campos_leitura[f"temp_{i}"] = _to_decimal_or_none(payload.get(f"temp_{i}"))

    # Químicos (opcionais)
    campos_quimicos = {
        "ph": _to_decimal_or_none(payload.get("ph")),
        "amonia": _to_decimal_or_none(payload.get("amonia")),
        "nitrito": _to_decimal_or_none(payload.get("nitrito")),
        "nitrato": _to_decimal_or_none(payload.get("nitrato")),
        "alcalinidade": _to_decimal_or_none(payload.get("alcalinidade")),
    }

    # Cria ou atualiza
    obj, created = ParametroAmbientalDiario.objects.get_or_create(
        fase=fase,
        data=data_alvo,
        defaults={**campos_leitura, **campos_quimicos}
    )

    if not created:
        for k, v in {**campos_leitura, **campos_quimicos}.items():
            setattr(obj, k, v)

    obj.save()  # recalcula médias/min/max/variação térmica automaticamente (save() do model)

    return JsonResponse({
        "success": True,
        "created": created,
        "data": {
            "id": obj.id,
            "fase_id": fase.id,
            "fase_nome": fase.nome,
            "data": obj.data.isoformat(),
            # leituras (eco para UI)
            "od_1": str(obj.od_1) if obj.od_1 is not None else None,
            "od_2": str(obj.od_2) if obj.od_2 is not None else None,
            "od_3": str(obj.od_3) if obj.od_3 is not None else None,
            "od_4": str(obj.od_4) if obj.od_4 is not None else None,
            "od_5": str(obj.od_5) if obj.od_5 is not None else None,
            "temp_1": str(obj.temp_1) if obj.temp_1 is not None else None,
            "temp_2": str(obj.temp_2) if obj.temp_2 is not None else None,
            "temp_3": str(obj.temp_3) if obj.temp_3 is not None else None,
            "temp_4": str(obj.temp_4) if obj.temp_4 is not None else None,
            "temp_5": str(obj.temp_5) if obj.temp_5 is not None else None,
            # químicos
            "ph": str(obj.ph) if obj.ph is not None else None,
            "amonia": str(obj.amonia) if obj.amonia is not None else None,
            "nitrito": str(obj.nitrito) if obj.nitrito is not None else None,
            "nitrato": str(obj.nitrato) if obj.nitrato is not None else None,
            "alcalinidade": str(obj.alcalinidade) if obj.alcalinidade is not None else None,
            # calculados
            "od_medio": str(obj.od_medio) if obj.od_medio is not None else None,
            "temp_media": str(obj.temp_media) if obj.temp_media is not None else None,
            "temp_min": str(obj.temp_min) if obj.temp_min is not None else None,
            "temp_max": str(obj.temp_max) if obj.temp_max is not None else None,
            "variacao_termica": str(obj.variacao_termica) if obj.variacao_termica is not None else None,
        }
    })


@login_required
@require_http_methods(["GET"])
@permission_required('producao.view_parametroambientaldiario', raise_exception=True)
def api_get_ambiente(request):
    """
    Retorna os parâmetros ambientais diários para uma data específica.
    Retorna um objeto com success e lista de fases.
    """
    data_str = request.GET.get("data")
    if not data_str:
        return JsonResponse({'success': False, 'message': 'Parâmetro "data" é obrigatório (AAAA-MM-DD).'}, status=400)

    try:
        data_alvo = datetime.strptime(data_str, "%Y-%m-%d").date()
    except ValueError:
        return JsonResponse({'success': False, 'message': 'Formato de data inválido. Use AAAA-MM-DD.'}, status=400)

    parametros = ParametroAmbientalDiario.objects.filter(data=data_alvo).select_related('fase')
    
    fases = []
    for p in parametros:
        fases.append({
            "id": p.id,
            "fase_id": p.fase.id,
            "fase_nome": p.fase.nome,
            "data": p.data.isoformat(),
            "od_medio": str(p.od_medio) if p.od_medio is not None else None,
            "temp_media": str(p.temp_media) if p.temp_media is not None else None,
            "temp_min": str(p.temp_min) if p.temp_min is not None else None,
            "temp_max": str(p.temp_max) if p.temp_max is not None else None,
            "variacao_termica": str(p.variacao_termica) if p.variacao_termica is not None else None,
            "ph": str(p.ph) if p.ph is not None else None,
            "amonia": str(p.amonia) if p.amonia is not None else None,
            "nitrito": str(p.nitrito) if p.nitrito is not None else None,
            "nitrato": str(p.nitrato) if p.nitrato is not None else None,
            "alcalinidade": str(p.alcalinidade) if p.alcalinidade is not None else None,
            "od_1": str(p.od_1) if p.od_1 is not None else None,
            "od_2": str(p.od_2) if p.od_2 is not None else None,
            "od_3": str(p.od_3) if p.od_3 is not None else None,
            "od_4": str(p.od_4) if p.od_4 is not None else None,
            "od_5": str(p.od_5) if p.od_5 is not None else None,
            "temp_1": str(p.temp_1) if p.temp_1 is not None else None,
            "temp_2": str(p.temp_2) if p.temp_2 is not None else None,
            "temp_3": str(p.temp_3) if p.temp_3 is not None else None,
            "temp_4": str(p.temp_4) if p.temp_4 is not None else None,
            "temp_5": str(p.temp_5) if p.temp_5 is not None else None,
        })
    return JsonResponse({
        'success': True,
        'data': data_str,
        'fases': fases
    })