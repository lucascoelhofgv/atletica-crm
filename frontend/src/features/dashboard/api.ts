import { keepPreviousData, queryOptions } from "@tanstack/react-query";

import { api } from "@/lib/api";
import { paraApi, type ParamsPeriodo } from "@/lib/periodo";

import type { Dashboard } from "./types";

export function dashboardQuery(periodo: ParamsPeriodo) {
  return queryOptions({
    queryKey: ["dashboard", periodo],
    queryFn: () => api<Dashboard>("dashboard/", { params: paraApi(periodo) }),
    // Ao trocar o período, mantém os dados antigos na tela até os novos
    // chegarem (o gráfico não pisca para skeleton).
    placeholderData: keepPreviousData,
    staleTime: 60_000,
  });
}
