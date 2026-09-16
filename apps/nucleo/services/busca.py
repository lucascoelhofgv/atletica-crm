"""Busca global (mesma da tela antiga, com links para o SPA)."""

from django.db.models import Q

from apps.catalogo.models import Produto
from apps.contas.models import Membro
from apps.crm.models import Cliente
from apps.fornecedores.models import Fornecedor
from apps.tarefas.models import Tarefa
from apps.vendas.models import Pedido

from .permissoes_busca import pode_ver


def buscar(termo: str, usuario, limite: int = 8) -> list[dict]:
    termo = (termo or "").strip()
    if len(termo) < 2:
        return []
    grupos = []

    if pode_ver(usuario, "crm"):
        qs = Cliente.objects.filter(
            Q(nome__icontains=termo) | Q(nome_social__icontains=termo) | Q(email__icontains=termo)
            | Q(telefone__icontains=termo) | Q(whatsapp__icontains=termo)
        )[:limite]
        grupos.append({"grupo": "clientes", "rotulo": "Clientes", "itens": [
            {"id": c.id, "titulo": c.nome_social or c.nome, "detalhe": c.email or c.whatsapp or c.telefone,
             "url": f"/clientes/{c.id}"} for c in qs]})

    if pode_ver(usuario, "catalogo"):
        qs = Produto.objects.filter(
            Q(nome__icontains=termo) | Q(codigo_interno__icontains=termo) | Q(sku__icontains=termo)
        )[:limite]
        grupos.append({"grupo": "produtos", "rotulo": "Produtos", "itens": [
            {"id": p.id, "titulo": str(p), "detalhe": f"{p.quantidade_atual} em estoque",
             "url": f"/produtos/{p.id}"} for p in qs]})

    if pode_ver(usuario, "vendas"):
        qs = Pedido.objects.select_related("cliente").filter(
            Q(numero__icontains=termo) | Q(cliente__nome__icontains=termo)
        )[:limite]
        grupos.append({"grupo": "pedidos", "rotulo": "Pedidos", "itens": [
            {"id": p.id, "titulo": p.numero or f"rascunho #{p.id}",
             "detalhe": f"{p.cliente} · {p.get_status_display()}", "url": f"/pedidos/{p.id}"} for p in qs]})

    if pode_ver(usuario, "fornecedores"):
        qs = Fornecedor.objects.filter(Q(nome__icontains=termo) | Q(nome_fantasia__icontains=termo))[:limite]
        grupos.append({"grupo": "fornecedores", "rotulo": "Fornecedores", "itens": [
            {"id": f.id, "titulo": str(f), "detalhe": f.get_categoria_display(),
             "url": f"/fornecedores/{f.id}"} for f in qs]})

    qs = Tarefa.objects.filter(titulo__icontains=termo)[:limite]
    grupos.append({"grupo": "tarefas", "rotulo": "Tarefas", "itens": [
        {"id": t.id, "titulo": t.titulo, "detalhe": t.get_status_display(), "url": f"/tarefas/{t.id}"} for t in qs]})

    if pode_ver(usuario, "membros"):
        qs = Membro.objects.filter(
            Q(first_name__icontains=termo) | Q(last_name__icontains=termo) | Q(username__icontains=termo)
        )[:limite]
        grupos.append({"grupo": "membros", "rotulo": "Membros", "itens": [
            {"id": m.id, "titulo": m.nome_exibicao, "detalhe": m.cargo or m.perfil_principal,
             "url": "/administracao/membros"} for m in qs]})

    return [g for g in grupos if g["itens"]]
