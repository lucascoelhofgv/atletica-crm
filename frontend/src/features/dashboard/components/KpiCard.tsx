import { Minus, TrendingDown, TrendingUp } from "lucide-react";
import { motion, useReducedMotion } from "motion/react";

import { Sparkline } from "@/components/charts/Sparkline";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { moeda, numero, percentual } from "@/lib/formatos";
import { cn } from "@/lib/utils";

import type { Kpi } from "../types";

export function KpiCard({
  id,
  rotulo,
  kpi,
  formato = "numero",
  comparar,
  indice = 0,
  /** Quando a queda é boa (ex.: custos). Aqui, tudo é "quanto maior, melhor". */
  invertido = false,
}: {
  id: string;
  rotulo: string;
  kpi: Kpi;
  formato?: "moeda" | "numero";
  comparar: boolean;
  indice?: number;
  invertido?: boolean;
}) {
  const reduzir = useReducedMotion();
  const formatar = formato === "moeda" ? moeda : numero;
  const variacao = kpi.variacao;
  const semBase = comparar && variacao === null;
  const positivo = variacao !== null && variacao > 0.0005;
  const negativo = variacao !== null && variacao < -0.0005;
  const bom = invertido ? negativo : positivo;
  const ruim = invertido ? positivo : negativo;

  return (
    <motion.div
      initial={reduzir ? false : { opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: indice * 0.05, duration: 0.3 }}
    >
      <Card className="gap-2 overflow-hidden py-4">
        <CardHeader className="px-4 pb-0">
          <div className="text-sm text-muted-foreground">{rotulo}</div>
          <div className="flex items-end justify-between gap-2">
            <div className="tabular font-display text-2xl font-semibold leading-none tracking-tight sm:text-[1.7rem]">
              {formatar(kpi.valor)}
            </div>
            {comparar && (
              <div
                className={cn(
                  "flex items-center gap-1 rounded-md px-1.5 py-0.5 text-xs font-medium",
                  bom && "bg-success/15 text-success",
                  ruim && "bg-destructive/15 text-destructive",
                  !bom && !ruim && "bg-muted text-muted-foreground",
                )}
                title={
                  kpi.anterior !== null
                    ? `Período anterior: ${formatar(kpi.anterior)}`
                    : undefined
                }
              >
                {positivo ? (
                  <TrendingUp className="size-3.5" />
                ) : negativo ? (
                  <TrendingDown className="size-3.5" />
                ) : (
                  <Minus className="size-3.5" />
                )}
                {semBase ? "sem base" : percentual(variacao)}
              </div>
            )}
          </div>
          {comparar && kpi.anterior !== null && (
            <div className="text-xs text-muted-foreground">
              anterior: <span className="tabular">{formatar(kpi.anterior)}</span>
            </div>
          )}
        </CardHeader>
        <CardContent className="px-2 pb-0">
          <Sparkline id={id} valores={kpi.serie} />
        </CardContent>
      </Card>
    </motion.div>
  );
}
