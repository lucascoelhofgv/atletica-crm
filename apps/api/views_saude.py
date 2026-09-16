"""Health check usado pelo Render (``healthCheckPath``). Sem autenticação e
sem tocar no banco, para responder rápido mesmo em cold start."""

from django.http import JsonResponse
from django.views.decorators.http import require_GET


@require_GET
def saude(request):
    return JsonResponse({"ok": True})


def nao_encontrado(request, *args, **kwargs):
    """Catch-all de ``/api/``: rota inexistente devolve 404 em JSON, não HTML."""
    return JsonResponse(
        {"erro": {"codigo": "nao_encontrado", "mensagem": "Rota não encontrada.",
                  "campos": {}}},
        status=404,
    )
