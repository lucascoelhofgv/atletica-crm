"""Erros da API sempre em JSON, no formato::

    {"erro": {"codigo": "...", "mensagem": "...", "campos": {"campo": ["msg"]}}}

Diferença importante em relação ao padrão do DRF: "não autenticado" devolve
**401** (o DRF devolve 403 quando a autenticação é por sessão), para o frontend
conseguir distinguir "precisa logar" de "não tem permissão".
"""

from rest_framework import exceptions, status
from rest_framework.response import Response
from rest_framework.views import exception_handler

CODIGOS = {
    400: "validacao",
    401: "nao_autenticado",
    403: "permissao_negada",
    404: "nao_encontrado",
    405: "metodo_nao_permitido",
    415: "tipo_nao_suportado",
    429: "muitas_requisicoes",
}

MENSAGENS = {
    "nao_autenticado": "Faça login para continuar.",
    "permissao_negada": "Você não tem permissão para esta ação.",
    "nao_encontrado": "Registro não encontrado.",
    "validacao": "Verifique os campos informados.",
}


def _texto(valor):
    """Achata listas/dicts de mensagens do DRF em uma string legível."""
    if isinstance(valor, (list, tuple)):
        return "; ".join(_texto(v) for v in valor if v)
    if isinstance(valor, dict):
        return "; ".join(_texto(v) for v in valor.values() if v)
    return str(valor)


def _desmontar(data):
    """Separa mensagem geral e erros por campo a partir de ``response.data``."""
    if isinstance(data, dict):
        campos = {}
        geral = []
        for chave, valor in data.items():
            if chave in ("detail", "non_field_errors"):
                geral.append(_texto(valor))
            else:
                # Listas de dicts (ex.: faltas de estoque por item) passam
                # intactas; o resto vira texto.
                campos[chave] = (
                    [v if isinstance(v, dict) else str(v) for v in valor]
                    if isinstance(valor, (list, tuple)) else [_texto(valor)]
                )
        return "; ".join(g for g in geral if g), campos
    return _texto(data), {}


def tratar(exc, context):
    resposta = exception_handler(exc, context)
    if resposta is None:
        return None  # erro inesperado: deixa o Django responder 500

    if isinstance(exc, (exceptions.NotAuthenticated, exceptions.AuthenticationFailed)):
        resposta.status_code = status.HTTP_401_UNAUTHORIZED

    codigo = CODIGOS.get(resposta.status_code, "erro")
    mensagem, campos = _desmontar(resposta.data)
    if not mensagem:
        mensagem = MENSAGENS.get(codigo, "Não foi possível concluir a operação.")

    resposta.data = {"erro": {"codigo": codigo, "mensagem": mensagem, "campos": campos}}
    return resposta


def erro_json(codigo, mensagem, status_code):
    """Atalho para views que respondem erro fora do fluxo de exceções do DRF."""
    return Response(
        {"erro": {"codigo": codigo, "mensagem": mensagem, "campos": {}}},
        status=status_code,
    )
