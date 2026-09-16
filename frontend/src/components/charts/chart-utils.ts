/**
 * Regras de gráfico do projeto (ver vault: padroes-dashboard):
 * - eixo Y ancorado em 0 para série não-negativa;
 * - ticks compactos em pt-BR ("R$ 1,2 mil"), valor completo só no tooltip;
 * - escala de tempo nunca distorcida: o servidor já faz zero-fill.
 */

import { format, parseISO } from "date-fns";
import { ptBR } from "date-fns/locale";

import { compacto, moedaCompacta } from "@/lib/formatos";

import type { Granularidade } from "@/features/dashboard/types";

export const tickCompacto = (v: number) => compacto(v);
export const tickMoeda = (v: number) => moedaCompacta(v);

/** Rótulo do eixo X: "15 set" por dia, "set/26" por mês. */
export function rotuloEixo(iso: string, granularidade: Granularidade) {
  const d = parseISO(iso);
  return granularidade === "mes" ? format(d, "MMM/yy", { locale: ptBR }) : format(d, "d MMM", { locale: ptBR });
}

/** Rótulo completo para o tooltip. */
export function rotuloPonto(iso: string, granularidade: Granularidade) {
  const d = parseISO(iso);
  return granularidade === "mes"
    ? format(d, "MMMM 'de' yyyy", { locale: ptBR })
    : format(d, "EEEE, d 'de' MMMM", { locale: ptBR });
}

/** Domínio Y "honesto": base 0, teto automático. */
export const DOMINIO_NAO_NEGATIVO: [number, string] = [0, "auto"];

/** Quantos rótulos cabem no eixo X sem se atropelar. */
export function intervaloTicks(nPontos: number, largura = 600) {
  const maximo = Math.max(3, Math.floor(largura / 70));
  return Math.max(0, Math.ceil(nPontos / maximo) - 1);
}

export const COR = {
  principal: "var(--chart-1)",
  anterior: "var(--muted-foreground)", // período anterior: cinza tracejado, nunca disputa com a métrica
  terciaria: "var(--chart-3)",
  alerta: "var(--chart-4)",
  extra: "var(--chart-5)",
} as const;
