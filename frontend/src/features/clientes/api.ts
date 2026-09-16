import { keepPreviousData, queryOptions } from "@tanstack/react-query";

import { api, montarUrl, type Paginado } from "@/lib/api";

import type {
  Cliente, ClienteEntrada, ClienteLista, FiltrosClientes, Interacao, OpcoesCliente,
} from "./types";

export const chaves = {
  todos: ["clientes"] as const,
  lista: (f: FiltrosClientes) => ["clientes", "lista", f] as const,
  detalhe: (id: number) => ["clientes", "detalhe", id] as const,
  opcoes: ["clientes", "opcoes"] as const,
};

export const clientesQuery = (filtros: FiltrosClientes) =>
  queryOptions({
    queryKey: chaves.lista(filtros),
    queryFn: () => api<Paginado<ClienteLista>>("clientes/", { params: { ...filtros } }),
    placeholderData: keepPreviousData,
  });

export const clienteQuery = (id: number) =>
  queryOptions({
    queryKey: chaves.detalhe(id),
    queryFn: () => api<Cliente>(`clientes/${id}/`),
  });

export const opcoesClienteQuery = queryOptions({
  queryKey: chaves.opcoes,
  queryFn: () => api<OpcoesCliente>("clientes/opcoes/"),
  staleTime: 10 * 60_000,
});

export const criarCliente = (dados: ClienteEntrada) =>
  api<Cliente>("clientes/", { method: "POST", body: dados });

export const atualizarCliente = (id: number, dados: Partial<ClienteEntrada>) =>
  api<Cliente>(`clientes/${id}/`, { method: "PATCH", body: dados });

export const excluirCliente = (id: number) => api<void>(`clientes/${id}/`, { method: "DELETE" });

export const registrarInteracao = (
  id: number,
  dados: { tipo: string; resumo: string; detalhe?: string; data?: string },
) => api<Interacao>(`clientes/${id}/interacoes/`, { method: "POST", body: dados });

export const excluirInteracao = (id: number, interacaoId: number) =>
  api<void>(`clientes/${id}/interacoes/${interacaoId}/`, { method: "DELETE" });

export const urlExportarClientes = (filtros: FiltrosClientes) =>
  montarUrl("clientes/exportar/", { ...filtros, pagina: undefined });
