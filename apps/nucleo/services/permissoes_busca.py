"""Atalho para a busca global não importar o módulo de permissões circularmente."""

from apps.nucleo.permissoes import pode_ler


def pode_ver(usuario, modulo: str) -> bool:
    return pode_ler(usuario, modulo)
