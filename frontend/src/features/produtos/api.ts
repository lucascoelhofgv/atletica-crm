import { keepPreviousData, queryOptions } from "@tanstack/react-query";

import { api, montarUrl, type Paginado } from "@/lib/api";

import type {
  FiltrosProdutos, Movimentacao, MovimentacaoEntrada, OpcoesProduto, Produto, ProdutoEntrada,
  ProdutoLista,
} from "./types";

export const chaves = {
  todos: ["produtos"] as const,
  lista: (f: FiltrosProdutos) => ["produtos", "lista", f] as const,
  detalhe: (id: number) => ["produtos", "detalhe", id] as const,
  opcoes: ["produtos", "opcoes"] as const,
  movimentacoes: (f: Record<string, unknown>) => ["movimentacoes", f] as const,
};

export const produtosQuery = (filtros: FiltrosProdutos) =>
  queryOptions({
    queryKey: chaves.lista(filtros),
    queryFn: () => api<Paginado<ProdutoLista>>("produtos/", { params: { ...filtros } }),
    placeholderData: keepPreviousData,
  });

export const produtoQuery = (id: number) =>
  queryOptions({ queryKey: chaves.detalhe(id), queryFn: () => api<Produto>(`produtos/${id}/`) });

export const opcoesProdutoQuery = queryOptions({
  queryKey: chaves.opcoes,
  queryFn: () => api<OpcoesProduto>("produtos/opcoes/"),
  staleTime: 10 * 60_000,
});

export const movimentacoesQuery = (filtros: { produto?: number; tipo?: string; pagina?: number }) =>
  queryOptions({
    queryKey: chaves.movimentacoes(filtros),
    queryFn: () => api<Paginado<Movimentacao>>("movimentacoes/", { params: { ...filtros, tamanho: 50 } }),
    placeholderData: keepPreviousData,
  });

/** Com foto vai multipart; sem foto vai JSON. */
function corpo(dados: Partial<ProdutoEntrada>, foto?: File | null) {
  if (foto === undefined) return dados;
  const fd = new FormData();
  for (const [k, v] of Object.entries(dados)) {
    if (v === undefined) continue;
    fd.append(k, v === null ? "" : String(v));
  }
  if (foto) fd.append("foto", foto);
  else fd.append("foto", "");
  return fd;
}

export const criarProduto = (dados: ProdutoEntrada, foto?: File | null) =>
  api<Produto>("produtos/", { method: "POST", body: corpo(dados, foto) });

export const atualizarProduto = (id: number, dados: Partial<ProdutoEntrada>, foto?: File | null) =>
  api<Produto>(`produtos/${id}/`, { method: "PATCH", body: corpo(dados, foto) });

export const excluirProduto = (id: number) => api<void>(`produtos/${id}/`, { method: "DELETE" });

export const movimentarEstoque = (id: number, dados: MovimentacaoEntrada) =>
  api<{ movimentacao: Movimentacao; produto: Produto }>(`produtos/${id}/movimentar/`, {
    method: "POST",
    body: dados,
  });

export const urlExportarProdutos = (filtros: FiltrosProdutos) =>
  montarUrl("produtos/exportar/", { ...filtros, pagina: undefined });
