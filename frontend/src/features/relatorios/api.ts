import { keepPreviousData, queryOptions } from "@tanstack/react-query";

import { api, montarUrl } from "@/lib/api";
import { paraApi, type ParamsPeriodo } from "@/lib/periodo";

import type { RelClientes, RelEstoque, RelProdutos, RelVendas } from "./types";

const comum = { placeholderData: keepPreviousData, staleTime: 60_000 } as const;

export const vendasQuery = (periodo: ParamsPeriodo) =>
  queryOptions({
    queryKey: ["relatorios", "vendas", periodo],
    queryFn: () => api<RelVendas>("relatorios/vendas/", { params: paraApi(periodo) }),
    ...comum,
  });

export const produtosQuery = (periodo: ParamsPeriodo) =>
  queryOptions({
    queryKey: ["relatorios", "produtos", periodo],
    queryFn: () => api<RelProdutos>("relatorios/produtos/", { params: paraApi(periodo) }),
    ...comum,
  });

export const estoqueQuery = (situacao?: string) =>
  queryOptions({
    queryKey: ["relatorios", "estoque", situacao ?? "todos"],
    queryFn: () =>
      api<RelEstoque>("relatorios/estoque/", {
        params: { situacao: situacao === "ok" ? undefined : situacao },
      }),
    ...comum,
  });

export const clientesQuery = (recorrentes: boolean) =>
  queryOptions({
    queryKey: ["relatorios", "clientes", recorrentes],
    queryFn: () =>
      api<RelClientes>("relatorios/clientes/", { params: { recorrentes: recorrentes ? 1 : undefined } }),
    ...comum,
  });

/** Link de download do mesmo relatório em CSV (abre direto, com a sessão). */
export function urlCsv(
  relatorio: "vendas" | "produtos" | "estoque" | "clientes",
  params: Record<string, string | number | boolean | null | undefined>,
) {
  return montarUrl(`relatorios/${relatorio}/`, { ...params, formato: "csv" });
}
