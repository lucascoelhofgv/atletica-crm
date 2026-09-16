import { Area, AreaChart, YAxis } from "recharts";

import { ChartContainer } from "@/components/ui/chart";

import { COR, DOMINIO_NAO_NEGATIVO } from "./chart-utils";

/** Mini-série sem eixos para os cards de KPI. Base em 0, como os gráficos grandes. */
export function Sparkline({
  valores,
  cor = COR.principal,
  altura = 40,
  id,
}: {
  valores: number[];
  cor?: string;
  altura?: number;
  id: string;
}) {
  const dados = valores.map((v, i) => ({ i, v }));
  const gradiente = `spark-${id}`;
  return (
    <ChartContainer config={{ v: { label: "" } }} className="aspect-auto w-full" style={{ height: altura }}>
      <AreaChart data={dados} margin={{ top: 2, right: 0, left: 0, bottom: 0 }}>
        <defs>
          <linearGradient id={gradiente} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={cor} stopOpacity={0.4} />
            <stop offset="100%" stopColor={cor} stopOpacity={0} />
          </linearGradient>
        </defs>
        <YAxis domain={DOMINIO_NAO_NEGATIVO} hide />
        <Area
          dataKey="v"
          type="monotone"
          stroke={cor}
          strokeWidth={1.5}
          fill={`url(#${gradiente})`}
          dot={false}
          isAnimationActive={false}
        />
      </AreaChart>
    </ChartContainer>
  );
}
