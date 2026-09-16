import { keepPreviousData, queryOptions } from "@tanstack/react-query";

import { api, type Paginado } from "@/lib/api";

import type {
  AvaliacaoEntrada, FiltrosFornecedores, Fornecedor, FornecedorEntrada, FornecedorLista, OpcoesFornecedor,
} from "./types";

export const chaves = {
  todos: ["fornecedores"] as const,
  lista: (f: FiltrosFornecedores) => ["fornecedores", "lista", f] as const,
  detalhe: (id: number) => ["fornecedores", "detalhe", id] as const,
  opcoes: ["fornecedores", "opcoes"] as const,
};

export const fornecedoresQuery = (filtros: FiltrosFornecedores) =>
  queryOptions({
    queryKey: chaves.lista(filtros),
    queryFn: () => api<Paginado<FornecedorLista>>("fornecedores/", { params: { ...filtros } }),
    placeholderData: keepPreviousData,
  });

export const fornecedorQuery = (id: number) =>
  queryOptions({ queryKey: chaves.detalhe(id), queryFn: () => api<Fornecedor>(`fornecedores/${id}/`) });

export const opcoesFornecedorQuery = queryOptions({
  queryKey: chaves.opcoes,
  queryFn: () => api<OpcoesFornecedor>("fornecedores/opcoes/"),
  staleTime: 10 * 60_000,
});

export const criarFornecedor = (d: FornecedorEntrada) => api<Fornecedor>("fornecedores/", { method: "POST", body: d });
export const atualizarFornecedor = (id: number, d: Partial<FornecedorEntrada>) =>
  api<Fornecedor>(`fornecedores/${id}/`, { method: "PATCH", body: d });
export const excluirFornecedor = (id: number) => api<void>(`fornecedores/${id}/`, { method: "DELETE" });
export const avaliarFornecedor = (id: number, d: AvaliacaoEntrada) =>
  api<Fornecedor>(`fornecedores/${id}/avaliacoes/`, { method: "POST", body: d });
export const excluirAvaliacao = (id: number, avaliacaoId: number) =>
  api<Fornecedor>(`fornecedores/${id}/avaliacoes/${avaliacaoId}/`, { method: "DELETE" });
export const enviarContrato = (id: number, arquivo: File | null) => {
  const fd = new FormData();
  if (arquivo) fd.append("contrato", arquivo);
  return api<Fornecedor>(`fornecedores/${id}/contrato/`, { method: "POST", body: fd });
};
