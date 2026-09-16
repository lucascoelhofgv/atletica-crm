import { keepPreviousData, queryOptions } from "@tanstack/react-query";

import { api, type Paginado } from "@/lib/api";

import type {
  CustoEntrada, Evento, EventoEntrada, EventoLista, FiltrosEventos, LoteEntrada, OpcoesEvento, ReceitaEntrada,
} from "./types";

export const chaves = {
  todos: ["eventos"] as const,
  lista: (f: FiltrosEventos) => ["eventos", "lista", f] as const,
  detalhe: (id: number) => ["eventos", "detalhe", id] as const,
  opcoes: ["eventos", "opcoes"] as const,
};

export const eventosQuery = (filtros: FiltrosEventos) =>
  queryOptions({
    queryKey: chaves.lista(filtros),
    queryFn: () => api<Paginado<EventoLista>>("eventos/", { params: { ...filtros } }),
    placeholderData: keepPreviousData,
  });

export const eventoQuery = (id: number) =>
  queryOptions({ queryKey: chaves.detalhe(id), queryFn: () => api<Evento>(`eventos/${id}/`) });

export const opcoesEventoQuery = queryOptions({
  queryKey: chaves.opcoes,
  queryFn: () => api<OpcoesEvento>("eventos/opcoes/"),
  staleTime: 10 * 60_000,
});

export const criarEvento = (d: EventoEntrada) => api<Evento>("eventos/", { method: "POST", body: d });
export const atualizarEvento = (id: number, d: Partial<EventoEntrada>) => api<Evento>(`eventos/${id}/`, { method: "PATCH", body: d });
export const excluirEvento = (id: number) => api<void>(`eventos/${id}/`, { method: "DELETE" });

export type TipoLinha = "lotes" | "custos" | "receitas";
type EntradaLinha = LoteEntrada | CustoEntrada | ReceitaEntrada;

export const adicionarLinha = (id: number, tipo: TipoLinha, d: EntradaLinha) =>
  api<Evento>(`eventos/${id}/${tipo}/`, { method: "POST", body: d });
export const alterarLinha = (id: number, tipo: TipoLinha, linhaId: number, d: Partial<EntradaLinha>) =>
  api<Evento>(`eventos/${id}/${tipo}/${linhaId}/`, { method: "PATCH", body: d });
export const removerLinha = (id: number, tipo: TipoLinha, linhaId: number) =>
  api<Evento>(`eventos/${id}/${tipo}/${linhaId}/`, { method: "DELETE" });
