"""Exporta as festas para a aba 'Festas' do Google Sheets. Agendável."""

from django.core.management.base import BaseCommand, CommandError

from apps.nucleo.sheets import SheetsIndisponivel


class Command(BaseCommand):
    help = "Sincroniza as festas com a aba 'Festas' do Google Sheets."

    def handle(self, *args, **options):
        from apps.eventos.sheets import exportar_festas

        try:
            n = exportar_festas()
        except SheetsIndisponivel as exc:
            raise CommandError(str(exc))
        self.stdout.write(self.style.SUCCESS(f"Aba 'Festas' atualizada ({n} evento(s))."))
