"""Prepara o banco para uso: perfis de acesso, categorias padrão, configuração
de identidade visual e (opcionalmente) dados de demonstração.

Uso:
    python manage.py seed_inicial                 # só estrutura
    python manage.py seed_inicial --com-demo      # estrutura + dados fictícios
    python manage.py seed_inicial --remover-demo  # apaga os dados fictícios
"""

from __future__ import annotations

import random
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.contas.models import (
    PERFIL_ADMIN, PERFIL_DIRETORIA, PERFIL_ESTOQUE, PERFIL_FINANCEIRO,
    PERFIL_OPERACIONAL, PERFIL_VISUALIZACAO,
)
from apps.catalogo.models import CategoriaProduto, MovimentacaoEstoque, Produto
from apps.crm.models import CategoriaCliente, Cliente, Tag
from apps.fornecedores.models import Fornecedor
from apps.nucleo.models import Configuracao
from apps.tarefas.models import Tarefa
from apps.vendas.models import ItemPedido, Pedido

User = get_user_model()

DEMO_TAG = "[DEMO]"  # marcador em observações para permitir remoção depois

PERMISSOES_LEITURA = ("view",)
PERMISSOES_EDICAO = ("view", "add", "change")
PERMISSOES_TOTAIS = ("view", "add", "change", "delete")

MAPA_PERFIS = {
    PERFIL_DIRETORIA: {
        "crm": PERMISSOES_EDICAO, "catalogo": PERMISSOES_EDICAO,
        "vendas": PERMISSOES_EDICAO, "fornecedores": PERMISSOES_EDICAO,
        "tarefas": PERMISSOES_TOTAIS, "nucleo": PERMISSOES_LEITURA,
        "contas": PERMISSOES_LEITURA,
    },
    PERFIL_OPERACIONAL: {
        "crm": PERMISSOES_EDICAO, "vendas": PERMISSOES_EDICAO,
        "tarefas": PERMISSOES_EDICAO, "catalogo": PERMISSOES_LEITURA,
        "fornecedores": PERMISSOES_LEITURA,
    },
    PERFIL_ESTOQUE: {
        "catalogo": PERMISSOES_TOTAIS, "fornecedores": PERMISSOES_LEITURA,
        "vendas": PERMISSOES_LEITURA, "tarefas": PERMISSOES_EDICAO,
    },
    PERFIL_FINANCEIRO: {
        "vendas": PERMISSOES_EDICAO, "crm": PERMISSOES_LEITURA,
        "catalogo": PERMISSOES_LEITURA, "fornecedores": PERMISSOES_LEITURA,
        "tarefas": PERMISSOES_EDICAO,
    },
    PERFIL_VISUALIZACAO: "somente_leitura",
}


class Command(BaseCommand):
    help = "Cria perfis, categorias, configuração e dados de demonstração."

    def add_arguments(self, parser):
        parser.add_argument("--com-demo", action="store_true",
                            help="também cria dados fictícios de demonstração")
        parser.add_argument("--remover-demo", action="store_true",
                            help="remove os dados de demonstração")

    @transaction.atomic
    def handle(self, *args, **opts):
        if opts["remover_demo"]:
            self._remover_demo()
            return

        self._perfis()
        self._configuracao()
        self._categorias()
        self.stdout.write(self.style.SUCCESS("Estrutura básica criada/atualizada."))

        if opts["com_demo"]:
            self._demo()
            self.stdout.write(self.style.SUCCESS("Dados de demonstração criados."))

        self.stdout.write(
            "\nPróximo passo: crie o administrador com\n"
            "    python manage.py createsuperuser\n"
            "e depois adicione esse usuário ao grupo 'Administrador'."
        )

    # ------------------------------------------------------------------ #
    def _perfis(self):
        admin_group, _ = Group.objects.get_or_create(name=PERFIL_ADMIN)
        admin_group.permissions.set(Permission.objects.all())

        for perfil, mapa in MAPA_PERFIS.items():
            grupo, _ = Group.objects.get_or_create(name=perfil)
            if mapa == "somente_leitura":
                perms = Permission.objects.filter(codename__startswith="view_")
                grupo.permissions.set(perms)
                continue
            perms = []
            for app_label, acoes in mapa.items():
                for acao in acoes:
                    perms += list(
                        Permission.objects.filter(
                            content_type__app_label=app_label,
                            codename__startswith=f"{acao}_",
                        )
                    )
            grupo.permissions.set(perms)
        self.stdout.write("  perfis de acesso: ok (6)")

    def _configuracao(self):
        cfg = Configuracao.carregar()
        if not cfg.nome_organizacao:
            cfg.nome_organizacao = "Atlética FGV Rio"
        cfg.save()
        self.stdout.write("  configuração de identidade: ok")

    def _categorias(self):
        for nome in ["Aluno FGV", "Ex-aluno", "Membro da Atlética", "Torcedor",
                     "Funcionário", "Parceiro", "Atleta", "Comissão técnica",
                     "Cliente externo"]:
            CategoriaCliente.objects.get_or_create(nome=nome)
        for nome in ["Vestuário", "Acessórios", "Bebidas", "Ingressos", "Outros"]:
            CategoriaProduto.objects.get_or_create(nome=nome)
        for nome in ["VIP", "Inadimplente", "Bateria", "Calouro"]:
            Tag.objects.get_or_create(nome=nome)
        self.stdout.write("  categorias e tags padrão: ok")

    # ------------------------------------------------------------------ #
    def _demo(self):
        random.seed(42)
        hoje = timezone.localdate()

        forn_confec, _ = Fornecedor.objects.get_or_create(
            nome="Uniformes Rio Ltda", defaults=dict(
                nome_fantasia="RioSport", categoria=Fornecedor.Categoria.CONFECCAO,
                contato_nome="Marina Souza", telefone="(21) 99999-0001",
                observacoes=DEMO_TAG),
        )
        forn_bebidas, _ = Fornecedor.objects.get_or_create(
            nome="Distribuidora Maracanã", defaults=dict(
                nome_fantasia="DistMara", categoria=Fornecedor.Categoria.BEBIDAS,
                contato_nome="João Lima", telefone="(21) 99999-0002",
                observacoes=DEMO_TAG),
        )

        cat_vest = CategoriaProduto.objects.get(nome="Vestuário")
        cat_acess = CategoriaProduto.objects.get(nome="Acessórios")
        produtos = []
        base = [
            ("Camiseta oficial 2026", cat_vest, forn_confec, 35, 79.9, "P", 40, 10),
            ("Camiseta oficial 2026", cat_vest, forn_confec, 35, 79.9, "M", 60, 15),
            ("Camiseta oficial 2026", cat_vest, forn_confec, 35, 79.9, "G", 25, 15),
            ("Moletom Atlética", cat_vest, forn_confec, 90, 189.9, "M", 18, 8),
            ("Moletom Atlética", cat_vest, forn_confec, 90, 189.9, "G", 4, 8),
            ("Boné bordado", cat_acess, forn_confec, 22, 59.9, "único", 0, 10),
            ("Caneca do time", cat_acess, forn_bebidas, 12, 34.9, "350ml", 50, 12),
            ("Ecobag", cat_acess, forn_confec, 9, 29.9, "único", 30, 10),
        ]
        for nome, cat, forn, custo, preco, tam, qtd, minimo in base:
            p = Produto.objects.create(
                nome=nome, categoria=cat, fornecedor=forn,
                custo_unitario=Decimal(str(custo)), preco_venda=Decimal(str(preco)),
                tamanho=tam, estoque_minimo=minimo, marca="Atlética FGV Rio",
                observacoes=DEMO_TAG,
            )
            if qtd:
                p.aplicar_movimentacao(
                    tipo=MovimentacaoEstoque.Tipo.ENTRADA, quantidade=qtd,
                    motivo="Carga inicial (demo)",
                )
            produtos.append(p)

        cats = list(CategoriaCliente.objects.all())
        nomes = ["Ana Prado", "Bruno Carvalho", "Carla Nunes", "Diego Alves",
                 "Elisa Ramos", "Felipe Costa", "Gabriela Dias", "Henrique Melo",
                 "Isabela Rocha", "João Pedro Assis", "Karina Lopes", "Lucas Vieira"]
        cursos = ["Administração", "Direito", "Economia", "RI", "Matemática Aplicada"]
        clientes = []
        for i, nome in enumerate(nomes):
            c = Cliente.objects.create(
                nome=nome,
                email=nome.lower().replace(" ", ".") + "@fgv.demo",
                telefone=f"(21) 98{random.randint(100,999)}-{random.randint(1000,9999)}",
                whatsapp="", curso=random.choice(cursos),
                periodo=f"{random.randint(1, 10)}º",
                campus="Botafogo", membro_fgv=True,
                categoria=random.choice(cats),
                relacionamento=random.choice(
                    [x[0] for x in Cliente.Relacionamento.choices]
                ),
                origem=random.choice(["Instagram", "Indicação", "Evento", "Balcão"]),
                observacoes=DEMO_TAG,
            )
            clientes.append(c)

        status_ciclo = [
            Pedido.Status.AGUARDANDO, Pedido.Status.PAGO, Pedido.Status.PRONTO,
            Pedido.Status.ENTREGUE, Pedido.Status.RASCUNHO, Pedido.Status.CANCELADO,
        ]
        for i in range(14):
            cliente = random.choice(clientes)
            ped = Pedido.objects.create(
                cliente=cliente,
                status=Pedido.Status.RASCUNHO,
                forma_pagamento=random.choice(
                    [x[0] for x in Pedido.FormaPagamento.choices]
                ),
                data_compra=hoje - timedelta(days=random.randint(0, 45)),
                local_retirada="Sala da Atlética",
                observacoes=DEMO_TAG,
            )
            for _ in range(random.randint(1, 3)):
                prod = random.choice(produtos)
                ItemPedido.objects.create(
                    pedido=ped, produto=prod,
                    quantidade=random.randint(1, 3),
                    preco_unitario=prod.preco_venda,
                )
            ped.status = status_ciclo[i % len(status_ciclo)]
            ped.recalcular_total()
            ped.save()
            try:
                ped.aplicar_efeito_estoque()
            except Exception:
                pass

        for titulo, prio, dias in [
            ("Fechar pedido de moletons com o fornecedor", Tarefa.Prioridade.ALTA, 3),
            ("Conferir estoque antes da bateria", Tarefa.Prioridade.URGENTE, -1),
            ("Enviar proposta de patrocínio para academia", Tarefa.Prioridade.NORMAL, 7),
            ("Atualizar planilha de caixa", Tarefa.Prioridade.NORMAL, 1),
            ("Divulgar venda de camisetas no Instagram", Tarefa.Prioridade.BAIXA, 5),
        ]:
            Tarefa.objects.create(
                titulo=titulo, prioridade=prio,
                prazo=hoje + timedelta(days=dias),
                status=Tarefa.Status.A_FAZER,
                descricao=DEMO_TAG,
            )

    def _remover_demo(self):
        n = 0
        for modelo in (Pedido, Tarefa, Produto, Cliente, Fornecedor):
            qs = modelo.objects.filter(observacoes__contains=DEMO_TAG) \
                if hasattr(modelo, "observacoes") else modelo.objects.none()
            if modelo is Tarefa:
                qs = modelo.objects.filter(descricao__contains=DEMO_TAG)
            n += qs.count()
            qs.delete()
        self.stdout.write(self.style.SUCCESS(f"Dados de demonstração removidos ({n})."))
