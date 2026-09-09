"""Disponibiliza a configuração de identidade visual em todos os templates."""

from .models import Configuracao


def configuracao(request):
    try:
        cfg = Configuracao.carregar()
    except Exception:
        cfg = None
    return {"cfg": cfg}
