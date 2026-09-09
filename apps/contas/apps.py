from django.apps import AppConfig


class ContasConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.contas"
    verbose_name = "Membros e acessos"

    def ready(self):
        from . import signals  # noqa: F401
