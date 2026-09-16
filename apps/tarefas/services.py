"""Lógica de tarefas compartilhada pela tela antiga e pela API."""

from django.db.models import Q
from django.utils import timezone

from apps.nucleo.models import registrar_atividade

from .models import ComentarioTarefa, Tarefa

ABERTAS = [Tarefa.Status.A_FAZER, Tarefa.Status.EM_ANDAMENTO, Tarefa.Status.AGUARDANDO]


def buscar(qs, termo: str):
    termo = (termo or "").strip()
    if not termo:
        return qs
    return qs.filter(Q(titulo__icontains=termo) | Q(descricao__icontains=termo))


def atrasadas(qs):
    return qs.filter(prazo__lt=timezone.localdate()).exclude(
        status__in=[Tarefa.Status.CONCLUIDA, Tarefa.Status.CANCELADA]
    )


def url_spa(t: Tarefa) -> str:
    return f"/tarefas/{t.pk}"


def mover(tarefa: Tarefa, novo: str, usuario) -> Tarefa:
    if novo not in dict(Tarefa.Status.choices):
        raise ValueError("Status inválido.")
    if tarefa.status == novo:
        return tarefa
    tarefa.status = novo
    tarefa.save()
    registrar_atividade(usuario, "moveu tarefa", f"{tarefa.titulo} → {tarefa.get_status_display()}",
                        url=url_spa(tarefa))
    return tarefa


def comentar(tarefa: Tarefa, texto: str, usuario) -> ComentarioTarefa:
    comentario = ComentarioTarefa.objects.create(tarefa=tarefa, autor=usuario, texto=texto)
    registrar_atividade(usuario, "comentou na tarefa", tarefa.titulo, url=url_spa(tarefa))
    return comentario


def registrar(usuario, verbo: str, tarefa: Tarefa):
    registrar_atividade(usuario, verbo, tarefa.titulo, url=url_spa(tarefa))
