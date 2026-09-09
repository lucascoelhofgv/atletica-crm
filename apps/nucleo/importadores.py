"""Importação de registros a partir de linhas de uma planilha (lista de dicts).

Cada importador:
* mapeia colunas por nome (sem acento, minúsculo), com apelidos;
* deduplica por uma chave estável (nome / e-mail / documento);
* cria ou atualiza, conforme o modo escolhido;
* devolve um resumo {criados, atualizados, ignorados, erros:[...]}.
"""

from __future__ import annotations

import unicodedata
from datetime import date


def _norm(texto: str) -> str:
    texto = (texto or "").strip().lower()
    texto = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in texto if not unicodedata.combining(c))


def _pega(reg: dict, *apelidos, normalizado: dict | None = None) -> str:
    """Retorna o valor da primeira coluna cujo nome bate com um dos apelidos."""
    if normalizado is None:
        normalizado = {_norm(k): v for k, v in reg.items()}
    for ap in apelidos:
        v = normalizado.get(_norm(ap))
        if v:
            return v.strip()
    return ""


def _resumo():
    return {"criados": 0, "atualizados": 0, "ignorados": 0, "erros": []}


# --------------------------------------------------------------------------- #
# Fornecedores  (ex.: planilha "Relação com Empresas")
# --------------------------------------------------------------------------- #
def importar_fornecedores(linhas, origem="planilha", modo="criar_atualizar",
                          categoria_padrao=None, usuario=None):
    from apps.fornecedores.models import Fornecedor

    if categoria_padrao is None:
        categoria_padrao = Fornecedor.Categoria.PATROCINIO

    r = _resumo()
    carimbo = f"Importado de {origem} em {date.today():%d/%m/%Y}."

    for i, reg in enumerate(linhas, start=2):  # linha 1 é o cabeçalho
        norm = {_norm(k): v for k, v in reg.items()}
        nome = _pega(reg, "empresa", "empresas", "nome", "razao social",
                     "fornecedor", "razao_social", normalizado=norm)
        if not nome:
            r["ignorados"] += 1
            continue

        dados = dict(
            nome_fantasia=_pega(reg, "nome fantasia", "fantasia", normalizado=norm),
            documento=_pega(reg, "cnpj", "cpf", "cnpj/cpf", "documento",
                            normalizado=norm),
            contato_nome=_pega(reg, "contato focal", "contato", "pessoa de contato",
                               "responsavel", normalizado=norm),
            email=_pega(reg, "e-mail", "email", "e-mails", "emails",
                        normalizado=norm).split(",")[0].strip(),
            telefone=_pega(reg, "telefone", "telefones", "celular", "whatsapp",
                           "contato telefonico", normalizado=norm),
            produtos_servicos=_pega(reg, "produtos", "servicos", "segmento",
                                    "area", normalizado=norm),
        )

        try:
            existente = Fornecedor.objects.filter(nome__iexact=nome).first()
            if existente:
                if modo == "somente_criar":
                    r["ignorados"] += 1
                    continue
                for campo, valor in dados.items():
                    if valor and not getattr(existente, campo):
                        setattr(existente, campo, valor)
                existente.save()
                r["atualizados"] += 1
            else:
                Fornecedor.objects.create(
                    nome=nome,
                    categoria=categoria_padrao,
                    status=Fornecedor.Status.ATIVO,
                    observacoes=carimbo,
                    criado_por=usuario if getattr(usuario, "pk", None) else None,
                    **dados,
                )
                r["criados"] += 1
        except Exception as exc:  # pragma: no cover
            r["erros"].append(f"linha {i} ({nome}): {exc}")

    return r


# --------------------------------------------------------------------------- #
# Clientes  (planilhas de membros, atletas, listas de contatos)
# --------------------------------------------------------------------------- #
def importar_clientes(linhas, origem="planilha", modo="criar_atualizar",
                      usuario=None):
    from apps.crm.models import CategoriaCliente, Cliente

    r = _resumo()

    for i, reg in enumerate(linhas, start=2):
        norm = {_norm(k): v for k, v in reg.items()}
        nome = _pega(reg, "nome", "nome completo", "aluno", "membro", "participante",
                     normalizado=norm)
        if not nome:
            r["ignorados"] += 1
            continue

        email = _pega(reg, "e-mail", "email", "e-mail fgv", "email fgv",
                      normalizado=norm).split(",")[0].strip()
        cat_nome = _pega(reg, "categoria", "tipo", "vinculo", normalizado=norm)
        categoria = None
        if cat_nome:
            categoria, _ = CategoriaCliente.objects.get_or_create(nome=cat_nome[:60])

        dados = dict(
            email=email,
            telefone=_pega(reg, "telefone", "celular", "contato", normalizado=norm),
            whatsapp=_pega(reg, "whatsapp", "zap", normalizado=norm),
            curso=_pega(reg, "curso", "graduacao", normalizado=norm),
            periodo=_pega(reg, "periodo", "semestre", normalizado=norm),
            campus=_pega(reg, "campus", "unidade", normalizado=norm),
            cidade=_pega(reg, "cidade", normalizado=norm),
            origem=origem,
        )
        if categoria:
            dados["categoria"] = categoria

        try:
            existente = None
            if email:
                existente = Cliente.objects.filter(email__iexact=email).first()
            if not existente:
                existente = Cliente.objects.filter(nome__iexact=nome).first()

            if existente:
                if modo == "somente_criar":
                    r["ignorados"] += 1
                    continue
                for campo, valor in dados.items():
                    if valor and not getattr(existente, campo):
                        setattr(existente, campo, valor)
                existente.save()
                r["atualizados"] += 1
            else:
                Cliente.objects.create(
                    nome=nome,
                    criado_por=usuario if getattr(usuario, "pk", None) else None,
                    **dados,
                )
                r["criados"] += 1
        except Exception as exc:  # pragma: no cover
            r["erros"].append(f"linha {i} ({nome}): {exc}")

    return r


IMPORTADORES = {
    "fornecedores": ("Fornecedores / Parceiros", importar_fornecedores),
    "clientes": ("Clientes", importar_clientes),
}
