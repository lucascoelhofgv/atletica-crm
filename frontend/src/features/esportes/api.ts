import { keepPreviousData, queryOptions } from "@tanstack/react-query";

import { api } from "@/lib/api";

import type { FontePlanilha, OpcoesFontes, ResultadoSincronizacao, ResumoEsportes } from "./types";

export const DESTINOS_ESPORTES = ["esportes_orcamento", "esportes_treinos"];

export const resumoEsportesQuery = (ano?: number, semestre?: number) =>
  queryOptions({
    queryKey: ["esportes", "resumo", ano ?? "padrao", semestre ?? "padrao"],
    queryFn: () => api<ResumoEsportes>("esportes/resumo/", { params: { ano, semestre } }),
    placeholderData: keepPreviousData,
    staleTime: 60_000,
  });

export const fontesQuery = queryOptions({
  queryKey: ["integracoes", "fontes"],
  queryFn: () => api<FontePlanilha[]>("integracoes/fontes/"),
});

export const opcoesFontesQuery = queryOptions({
  queryKey: ["integracoes", "fontes", "opcoes"],
  queryFn: () => api<OpcoesFontes>("integracoes/fontes/opcoes/"),
  staleTime: 5 * 60_000,
});

/** Baixar e ler a planilha no Google leva alguns segundos. */
export const sincronizarFonte = (id: number, simular = false) =>
  api<ResultadoSincronizacao>(`integracoes/fontes/${id}/${simular ? "simular" : "sincronizar"}/`, {
    method: "POST",
    timeoutMs: 120_000,
  });
