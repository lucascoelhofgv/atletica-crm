"""Importa para o CRM as planilhas cadastradas em Fontes de Planilha.

Feito para rodar sozinho (Render Cron Job, GitHub Actions, cron da máquina)::

    python manage.py importar_planilhas

Sem argumentos, percorre todas as fontes ativas. Cada fonte guarda o resultado
da última execução, então dá para ver pelo Django Admin o que rodou e o que
falhou. Uma fonte que quebra não impede as seguintes: o comando tenta todas e
só no fim avisa que houve falha.

Precisa da credencial do Google (ver apps/nucleo/sheets.py).
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from apps.nucleo.models import FontePlanilha
from apps.nucleo.services import integracoes


class Command(BaseCommand):
    help = "Importa as planilhas cadastradas (Fontes de Planilha) para o CRM."

    def add_arguments(self, parser):
        parser.add_argument(
            "--fonte",
            type=int,
            default=None,
            help="Importa apenas a fonte com este ID, mesmo se estiver desativada.",
        )
        parser.add_argument(
            "--simular",
            action="store_true",
            help="Lê a planilha e mostra o que viria, sem gravar nada no banco.",
        )

    def handle(self, *args, **opts):
        fontes = self._selecionar(opts["fonte"])
        if not fontes:
            self.stdout.write("Nenhuma fonte ativa cadastrada. Nada a fazer.")
            return

        falhas = 0
        for fonte in fontes:
            if not self._processar(fonte, opts["simular"]):
                falhas += 1

        if falhas:
            raise CommandError(
                f"{falhas} de {len(fontes)} fonte(s) falharam. Veja os erros acima."
            )
        self.stdout.write(self.style.SUCCESS(f"{len(fontes)} fonte(s) processada(s)."))

    def _selecionar(self, fonte_id):
        if fonte_id:
            fontes = list(FontePlanilha.objects.filter(pk=fonte_id))
            if not fontes:
                raise CommandError(f"Fonte {fonte_id} não encontrada.")
            return fontes
        return list(FontePlanilha.objects.filter(ativa=True))

    def _processar(self, fonte, simular):
        rotulo = f"{fonte.nome} [{fonte.get_destino_display()}]"
        try:
            resumo = self._executar(fonte, simular)
        except Exception as exc:
            self.stderr.write(self.style.ERROR(f"  {rotulo}: {exc}"))
            if not simular:
                fonte.ultimo_erro = str(exc)[:255]
                fonte.save(update_fields=["ultimo_erro"])
            return False

        self.stdout.write(self.style.SUCCESS(f"  {rotulo}: {resumo}"))
        if not simular:
            fonte.ultima_sincronizacao = timezone.now()
            fonte.ultimo_resultado = resumo[:255]
            fonte.ultimo_erro = ""
            fonte.save(
                update_fields=["ultima_sincronizacao", "ultimo_resultado", "ultimo_erro"]
            )
        return True

    def _executar(self, fonte, simular) -> str:
        """Chama o importador do destino e devolve uma linha de resumo."""
        if fonte.destino == FontePlanilha.Destino.CONTROLE_PRODUTOS:
            if simular:
                p = integracoes.previa_controle_produtos(fonte.planilha)
                return (
                    f"{p['produtos']} produto(s), {p['compras_recebidas']} de "
                    f"{p['compras_total']} compra(s) recebida(s), {p['vendas']} venda(s)"
                )
            r = integracoes.importar_controle_produtos(fonte.planilha, usuario=None)
            return ", ".join(
                f"{aba} {dados['criados']} novo(s)" for aba, dados in r.items()
            )

        if simular:
            p = integracoes.previa_importacao(fonte.planilha, fonte.aba, fonte.destino)
            return f"{p['total_linhas']} linha(s) em {len(p['cabecalho'])} coluna(s)"

        r = integracoes.importar(
            fonte.planilha, fonte.aba, fonte.destino, fonte.modo, usuario=None
        )
        resumo = (
            f"{r['criados']} criado(s), {r['atualizados']} atualizado(s), "
            f"{r['ignorados']} ignorado(s)"
        )
        if r.get("erros"):
            resumo += f", {len(r['erros'])} erro(s)"
        return resumo
