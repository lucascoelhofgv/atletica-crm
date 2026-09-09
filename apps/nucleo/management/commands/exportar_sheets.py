"""Exporta Clientes, Produtos e Pedidos para a planilha do Google configurada.

Pode ser agendado (Render Cron Job / GitHub Actions) para sincronização
periódica. Ver apps/nucleo/sheets.py para a configuração necessária.
"""

from django.core.management.base import BaseCommand, CommandError

from apps.nucleo.sheets import SheetsIndisponivel, exportar_tudo


class Command(BaseCommand):
    help = "Sincroniza dados do CRM com o Google Sheets."

    def handle(self, *args, **options):
        try:
            resumo = exportar_tudo()
        except SheetsIndisponivel as exc:
            raise CommandError(str(exc))
        for aba, qtd in resumo.items():
            self.stdout.write(self.style.SUCCESS(f"  {aba}: {qtd} linha(s)"))
        self.stdout.write(self.style.SUCCESS("Exportação concluída."))
