import { keepPreviousData, queryOptions } from "@tanstack/react-query";

import { api, type Paginado } from "@/lib/api";

import type { Coluna, FiltrosTarefas, OpcoesTarefa, StatusTarefa, Tarefa, TarefaCartao, TarefaEntrada } from "./types";

export const chaves = {
  todos: ["tarefas"] as const,
  lista: (f: FiltrosTarefas) => ["tarefas", "lista", f] as const,
  quadro: (f: FiltrosTarefas) => ["tarefas", "quadro", f] as const,
  detalhe: (id: number) => ["tarefas", "detalhe", id] as const,
  opcoes: ["tarefas", "opcoes"] as const,
};

export const tarefasQuery = (filtros: FiltrosTarefas) =>
  queryOptions({
    queryKey: chaves.lista(filtros),
    queryFn: () => api<Paginado<TarefaCartao>>("tarefas/", { params: { ...filtros, tamanho: 50 } }),
    placeholderData: keepPreviousData,
  });

export const quadroQuery = (filtros: FiltrosTarefas) =>
  queryOptions({
    queryKey: chaves.quadro(filtros),
    queryFn: () => api<{ colunas: Coluna[] }>("tarefas/quadro/", { params: { ...filtros } }),
    placeholderData: keepPreviousData,
  });

export const tarefaQuery = (id: number) =>
  queryOptions({ queryKey: chaves.detalhe(id), queryFn: () => api<Tarefa>(`tarefas/${id}/`) });

export const opcoesTarefaQuery = queryOptions({
  queryKey: chaves.opcoes,
  queryFn: () => api<OpcoesTarefa>("tarefas/opcoes/"),
  staleTime: 10 * 60_000,
});

export const criarTarefa = (d: TarefaEntrada) => api<Tarefa>("tarefas/", { method: "POST", body: d });
export const atualizarTarefa = (id: number, d: Partial<TarefaEntrada>) => api<Tarefa>(`tarefas/${id}/`, { method: "PATCH", body: d });
export const excluirTarefa = (id: number) => api<void>(`tarefas/${id}/`, { method: "DELETE" });
export const moverTarefa = (id: number, status: StatusTarefa) => api<Tarefa>(`tarefas/${id}/mover/`, { method: "POST", body: { status } });
export const comentarTarefa = (id: number, texto: string) => api<Tarefa>(`tarefas/${id}/comentarios/`, { method: "POST", body: { texto } });
export const excluirComentario = (id: number, cid: number) => api<Tarefa>(`tarefas/${id}/comentarios/${cid}/`, { method: "DELETE" });
export const enviarAnexo = (id: number, arquivo: File | null) => {
  const fd = new FormData();
  if (arquivo) fd.append("anexo", arquivo);
  return api<Tarefa>(`tarefas/${id}/anexo/`, { method: "POST", body: fd });
};
