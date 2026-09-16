import { Area, Bar, CartesianGrid, ComposedChart, Line, Tooltip, XAxis, YAxis } from "recharts";

import { ChartContainer, type ChartConfig } from "@/components/ui/chart";
import type { Granularidade, PontoSerie } from "@/features/dashboard/types";
import { moeda, numero } from "@/lib/formatos";

import { COR, DOMINIO_NAO_NEGATIVO, rotuloEixo, rotuloPonto, tickCompacto, tickMoeda } from "./chart-utils";

export interface GraficoSerieProps {
  dados: PontoSerie[];
  granularidade: Granularidade;
  /** Nome da métrica (aparece no tooltip). */
  rotulo: string;
  tipo?: "area" | "barras";
  formato?: "moeda" | "numero";
  comparar?: boolean;
  /** Altura em px (padrão 260). */
  altura?: number;
  cor?: string;
}

const config: ChartConfig = {
  valor: { label: "Atual" },
  anterior: { label: "Período anterior" },
};

interface ItemTooltip {
  dataKey?: string | number;
  value?: number | string;
  color?: string;
  payload?: PontoSerie;
}

function TooltipSerie({
  active,
  payload,
  granularidade,
  rotulo,
  formatar,
  comparar,
}: {
  active?: boolean;
  payload?: ReadonlyArray<ItemTooltip>;
  granularidade: Granularidade;
  rotulo: string;
  formatar: (v: number) => string;
  comparar: boolean;
}) {
  if (!active || !payload?.length) return null;
  const ponto = payload[0]?.payload;
  if (!ponto) return null;
  const anterior = ponto.anterior;
  return (
    <div className="rounded-lg border bg-popover px-3 py-2 text-xs shadow-md">
      <div className="mb-1 font-medium capitalize text-popover-foreground">
        {rotuloPonto(ponto.data, granularidade)}
      </div>
      <div className="flex items-center justify-between gap-6">
        <span className="flex items-center gap-1.5 text-muted-foreground">
          <span className="size-2 rounded-full" style={{ background: COR.principal }} />
          {rotulo}
        </span>
        <span className="tabular font-medium">{formatar(Number(ponto.valor))}</span>
      </div>
      {comparar && anterior !== undefined && anterior !== null && (
        <div className="mt-0.5 flex items-center justify-between gap-6">
          <span className="flex items-center gap-1.5 text-muted-foreground">
            <span className="size-2 rounded-full" style={{ background: COR.anterior }} />
            Anterior
          </span>
          <span className="tabular text-muted-foreground">{formatar(Number(anterior))}</span>
        </div>
      )}
    </div>
  );
}

export function GraficoSerie({
  dados,
  granularidade,
  rotulo,
  tipo = "area",
  formato = "numero",
  comparar = false,
  altura = 260,
  cor = COR.principal,
}: GraficoSerieProps) {
  const formatar = formato === "moeda" ? moeda : numero;
  const tick = formato === "moeda" ? tickMoeda : tickCompacto;
  const idGradiente = `grad-${rotulo.replace(/\W+/g, "-")}`;

  return (
    <ChartContainer config={config} className="aspect-auto w-full" style={{ height: altura }}>
      <ComposedChart data={dados} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
        <defs>
          <linearGradient id={idGradiente} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={cor} stopOpacity={0.35} />
            <stop offset="100%" stopColor={cor} stopOpacity={0.02} />
          </linearGradient>
        </defs>
        <CartesianGrid vertical={false} strokeDasharray="3 3" stroke="var(--border)" />
        <XAxis
          dataKey="data"
          tickFormatter={(v: string) => rotuloEixo(v, granularidade)}
          tickLine={false}
          axisLine={false}
          minTickGap={28}
          interval="preserveStartEnd"
          tick={{ fontSize: 11 }}
          tickMargin={8}
        />
        <YAxis
          domain={DOMINIO_NAO_NEGATIVO}
          allowDecimals={false}
          tickFormatter={(v: number) => tick(v)}
          tickLine={false}
          axisLine={false}
          width={formato === "moeda" ? 64 : 40}
          tick={{ fontSize: 11 }}
        />
        <Tooltip
          cursor={{ stroke: "var(--border)" }}
          content={
            <TooltipSerie
              granularidade={granularidade}
              rotulo={rotulo}
              formatar={formatar}
              comparar={comparar}
            />
          }
        />
        {tipo === "barras" ? (
          <Bar dataKey="valor" fill={cor} radius={[4, 4, 0, 0]} maxBarSize={28} isAnimationActive />
        ) : (
          <Area
            dataKey="valor"
            type="monotone"
            stroke={cor}
            strokeWidth={2}
            fill={`url(#${idGradiente})`}
            dot={false}
            activeDot={{ r: 4 }}
          />
        )}
        {comparar && (
          <Line
            dataKey="anterior"
            type="monotone"
            stroke={COR.anterior}
            strokeWidth={1.5}
            strokeDasharray="4 4"
            dot={false}
            activeDot={{ r: 3 }}
          />
        )}
      </ComposedChart>
    </ChartContainer>
  );
}
