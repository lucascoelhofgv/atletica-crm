/**
 * Período global de análise, guardado na URL (search params) para link
 * compartilhado abrir a mesma visão. Validado na rota `/_auth`, então vale
 * para todas as telas logadas. O servidor resolve as datas de cada preset
 * (apps/nucleo/services/periodos.py); aqui só passamos os parâmetros.
 */

import { useNavigate, useSearch } from "@tanstack/react-router";
import { z } from "zod";

export const PRESETS = [
  { chave: "hoje", rotulo: "Hoje" },
  { chave: "7d", rotulo: "7 dias" },
  { chave: "30d", rotulo: "30 dias" },
  { chave: "semestre", rotulo: "Semestre" },
  { chave: "ano", rotulo: "Ano" },
] as const;

export type ChavePeriodo = (typeof PRESETS)[number]["chave"] | "custom";

const dataIso = z.string().regex(/^\d{4}-\d{2}-\d{2}$/);

export const periodoSearchSchema = z.object({
  periodo: z
    .enum(["hoje", "7d", "30d", "semestre", "ano", "custom"])
    .optional()
    .catch(undefined),
  inicio: dataIso.optional().catch(undefined),
  fim: dataIso.optional().catch(undefined),
  comparar: z.boolean().optional().catch(undefined),
});

export type BuscaPeriodo = z.infer<typeof periodoSearchSchema>;
export const CHAVES_PERIODO = ["periodo", "inicio", "fim", "comparar"] as const;

export interface ParamsPeriodo {
  periodo: ChavePeriodo;
  inicio?: string;
  fim?: string;
  comparar: boolean;
}

export function normalizar(busca: BuscaPeriodo): ParamsPeriodo {
  const periodo = busca.periodo ?? "30d";
  return {
    periodo,
    inicio: periodo === "custom" ? busca.inicio : undefined,
    fim: periodo === "custom" ? busca.fim : undefined,
    comparar: busca.comparar === true,
  };
}

/** Só o que precisa ir na URL (padrões e falsos ficam de fora). */
export function paraBusca(p: ParamsPeriodo): BuscaPeriodo {
  return {
    periodo: p.periodo === "30d" ? undefined : p.periodo,
    inicio: p.periodo === "custom" ? p.inicio : undefined,
    fim: p.periodo === "custom" ? p.fim : undefined,
    comparar: p.comparar ? true : undefined,
  };
}

/** Query string para a API (`?periodo=7d&comparar=1`). */
export function paraApi(p: ParamsPeriodo) {
  return {
    periodo: p.periodo,
    inicio: p.inicio,
    fim: p.fim,
    comparar: p.comparar ? 1 : undefined,
  };
}

export function usePeriodo() {
  const busca = useSearch({ from: "/_auth" });
  const navigate = useNavigate();
  const valores = normalizar(busca);

  function definir(patch: Partial<ParamsPeriodo>) {
    const novo = { ...valores, ...patch };
    void navigate({
      to: ".",
      search: (anterior: Record<string, unknown>) => ({ ...anterior, ...paraBusca(novo) }),
      replace: true,
    });
  }

  return { valores, definir };
}
