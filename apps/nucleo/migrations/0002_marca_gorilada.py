"""Identidade visual da Atlética Gorilada FGV como padrão da Configuração.

Além de trocar os defaults dos campos, atualiza o registro existente quando ele
ainda está com os valores antigos (nunca sobrescreve algo personalizado pelo admin).
"""

from django.db import migrations, models

ANTIGOS = {
    "nome_organizacao": ("Atlética FGV Rio", "Atlética Gorilada FGV"),
    "cor_primaria": ("#1B2A4A", "#182A76"),
    "cor_secundaria": ("#F4B400", "#FFE104"),
}


def aplicar_marca(apps, schema_editor):
    Configuracao = apps.get_model("nucleo", "Configuracao")
    for cfg in Configuracao.objects.all():
        mudou = False
        for campo, (antigo, novo) in ANTIGOS.items():
            atual = (getattr(cfg, campo) or "").strip()
            if not atual or atual.lower() == antigo.lower():
                setattr(cfg, campo, novo)
                mudou = True
        if not cfg.modo_escuro_disponivel:
            cfg.modo_escuro_disponivel = True   # o painel novo é escuro por padrão
            mudou = True
        if mudou:
            cfg.save()


class Migration(migrations.Migration):

    dependencies = [
        ("nucleo", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="configuracao",
            name="nome_organizacao",
            field=models.CharField(default="Atlética Gorilada FGV", max_length=120, verbose_name="nome da organização"),
        ),
        migrations.AlterField(
            model_name="configuracao",
            name="cor_primaria",
            field=models.CharField(default="#182A76", max_length=7, verbose_name="cor primária"),
        ),
        migrations.AlterField(
            model_name="configuracao",
            name="cor_secundaria",
            field=models.CharField(default="#FFE104", max_length=7, verbose_name="cor secundária"),
        ),
        migrations.AlterField(
            model_name="configuracao",
            name="modo_escuro_disponivel",
            field=models.BooleanField(default=True, verbose_name="disponibilizar modo escuro"),
        ),
        migrations.RunPython(aplicar_marca, migrations.RunPython.noop),
    ]
