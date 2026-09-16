import { Bar, BarChart, Tooltip, XAxis, YAxis } from "recharts";

import { ChartContainer } from "@/components/ui/chart";
import { numero } from "@/lib/formatos";

import { COR } from "./chart-utils";

export interface LinhaBarra {
  nome: string;
  valor: number;
  /** Texto extra no tooltip (ex.: receita formatada). */
  detalhe?: string;
}

function TooltipBarras({
  active,
  payload,
  rotuloValor,
}: {
  active?: boolean;
  payload?: ReadonlyArray<{ payload?: LinhaBarra }>;
  rotuloValor: string;
}) {
  const linha = payload?.[0]?.payload;
  if (!active || !linha) return null;
  return (
    <div className="rounded-lg border bg-popover px-3 py-2 text-xs shadow-md">
      <div className="mb-0.5 font-medium">{linha.nome}</div>
      <div className="text-muted-foreground">
        {rotuloValor}: <span className="tabular font-medium text-foreground">{numero(linha.valor)}</span>
      </div>
      {linha.detalhe && <div className="text-muted-foreground">{linha.detalhe}</div>}
    </div>
  );
}

/** Ranking horizontal (top produtos etc.). */
export function GraficoBarras({
  dados,
  rotuloValor = "Quantidade",
  cor = COR.principal,
  alturaLinha = 34,
}: {
  dados: LinhaBarra[];
  rotuloValor?: string;
  cor?: string;
  alturaLinha?: number;
}) {
  const altura = Math.max(120, dados.length * alturaLinha + 16);
  return (
    <ChartContainer config={{ valor: { label: rotuloValor } }} className="aspect-auto w-full" style={{ height: altura }}>
      <BarChart data={dados} layout="vertical" margin={{ top: 4, right: 12, left: 4, bottom: 4 }} barCategoryGap={8}>
        <XAxis type="number" hide domain={[0, "auto"]} />
        <YAxis
          type="category"
          dataKey="nome"
          width={120}
          tickLine={false}
          axisLine={false}
          tick={{ fontSize: 12 }}
          tickFormatter={(v: string) => (v.length > 18 ? `${v.slice(0, 17)}…` : v)}
        />
        <Tooltip cursor={{ fill: "var(--accent)", opacity: 0.4 }} content={<TooltipBarras rotuloValor={rotuloValor} />} />
        <Bar dataKey="valor" fill={cor} radius={[0, 4, 4, 0]} maxBarSize={22} />
      </BarChart>
    </ChartContainer>
  );
}
