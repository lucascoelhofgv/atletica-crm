"""Cria (ou atualiza) o usuário administrador a partir de variáveis de ambiente.

Serve para provisionar o primeiro acesso em plataformas sem terminal/shell
(ex.: Render no plano free). É idempotente: pode rodar em todo deploy.

Variáveis lidas:
    ADMIN_USERNAME   (obrigatória para criar)
    ADMIN_EMAIL      (opcional)
    ADMIN_PASSWORD   (obrigatória para criar; se mudar, a senha é atualizada)

Se ADMIN_USERNAME não estiver definida, o comando não faz nada e sai com sucesso
(assim pode ficar no build.sh sem quebrar nada).
"""

import os

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand

from apps.contas.models import PERFIL_ADMIN


class Command(BaseCommand):
    help = "Provisiona o usuário administrador via variáveis de ambiente."

    def handle(self, *args, **options):
        username = os.environ.get("ADMIN_USERNAME", "").strip()
        if not username:
            self.stdout.write("ADMIN_USERNAME não definida — nada a fazer.")
            return

        email = os.environ.get("ADMIN_EMAIL", "").strip()
        password = os.environ.get("ADMIN_PASSWORD", "")

        User = get_user_model()
        user, criado = User.objects.get_or_create(
            username=username,
            defaults={"email": email or f"{username}@atletica.local"},
        )

        if criado:
            if not password:
                user.delete()
                self.stderr.write(
                    "ADMIN_PASSWORD é obrigatória para criar o admin. Abortado."
                )
                return
            user.set_password(password)
            self.stdout.write(self.style.SUCCESS(f"Admin '{username}' criado."))
        else:
            # usuário já existe: só atualiza a senha se ADMIN_PASSWORD foi passada
            if password and not user.check_password(password):
                user.set_password(password)
                self.stdout.write(f"Senha do admin '{username}' atualizada.")
            else:
                self.stdout.write(f"Admin '{username}' já existe — mantido.")

        if email and user.email != email:
            user.email = email
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.save()

        grupo, _ = Group.objects.get_or_create(name=PERFIL_ADMIN)
        user.groups.add(grupo)
        self.stdout.write(self.style.SUCCESS("Admin no perfil 'Administrador'. OK."))
