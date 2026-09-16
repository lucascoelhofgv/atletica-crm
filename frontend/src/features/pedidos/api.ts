import { keepPreviousData, queryOptions } from "@tanstack/react-query";

import { api, type Paginado } from "@/lib/api";

import type { FiltrosPedidos, OpcoesPedido, Pedido, PedidoEntrada, PedidoLista, StatusPedido } from "./types";

export const chaves = {
  todos: ["pedidos"] as const,
  lista: (f: FiltrosPedidos) => ["pedidos", "lista", f] as const,
  detalhe: (id: number) => ["pedidos", "detalhe", id] as const,
  opcoes: ["pedidos", "opcoes"] as const,
};

export const pedidosQuery = (filtros: FiltrosPedidos) =>
  queryOptions({
    queryKey: chaves.lista(filtros),
    queryFn: () => api<Paginado<PedidoLista>>("pedidos/", { params: { ...filtros } }),
    placeholderData: keepPreviousData,
  });

export const pedidoQuery = (id: number) =>
  queryOptions({ queryKey: chaves.detalhe(id), queryFn: () => api<Pedido>(`pedidos/${id}/`) });

export const opcoesPedidoQuery = queryOptions({
  queryKey: chaves.opcoes,
  queryFn: () => api<OpcoesPedido>("pedidos/opcoes/"),
  staleTime: 10 * 60_000,
});

export const criarPedido = (dados: PedidoEntrada) => api<Pedido>("pedidos/", { method: "POST", body: dados });

export const atualizarPedido = (id: number, dados: Partial<PedidoEntrada>) =>
  api<Pedido>(`pedidos/${id}/`, { method: "PATCH", body: dados });

export const excluirPedido = (id: number) => api<void>(`pedidos/${id}/`, { method: "DELETE" });

export const mudarStatusPedido = (id: number, status: StatusPedido) =>
  api<Pedido>(`pedidos/${id}/status/`, { method: "POST", body: { status } });

export const registrarPagamento = (
  id: number,
  dados: { valor: number; forma: string; data?: string; observacao?: string },
) => api<Pedido>(`pedidos/${id}/pagamentos/`, { method: "POST", body: dados });

export const excluirPagamento = (id: number, pagamentoId: number) =>
  api<Pedido>(`pedidos/${id}/pagamentos/${pagamentoId}/`, { method: "DELETE" });

export const enviarComprovante = (id: number, arquivo: File | null) => {
  const fd = new FormData();
  if (arquivo) fd.append("comprovante", arquivo);
  return api<Pedido>(`pedidos/${id}/comprovante/`, { method: "POST", body: fd });
};
