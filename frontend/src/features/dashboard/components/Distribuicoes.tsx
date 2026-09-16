import { Vazio } from "@/components/estado";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { moeda, numero } from "@/lib/formatos";
import { cn } from "@/lib/utils";

import type { Distribuicao } from "../types";

const COR_STATUS: Record<string, string> = {
  pago: "var(--chart-3)",
  entregue: "var(--chart-3)",
  em_separacao: "var(--chart-1)",
  pronto: "var(--chart-1)",
  aguardando_pagamento: "var(--warning)",
  rascunho: "var(--muted-foreground)",
  cancelado: "var(--chart-4)",
  devolvido: "var(--chart-4)",
};

function Barras({ linhas, chave }: { linhas: Distribuicao[]; chave: "status" | "forma" }) {
  const total = linhas.reduce((s, l) => s + l.qtd, 0);
  if (!total) {
    return <Vazio titulo="Nenhum pedido no período" className="py-8" />;
  }
  return (
    <ul className="space-y-2.5">
      {linhas.map((l, i) => {
        const pct = total ? l.qtd / total : 0;
        const cor = chave === "status" ? COR_STATUS[l.status ?? ""] ?? "var(--chart-5)" : `var(--chart-${(i % 5) + 1})`;
        return (
          <li key={l.status ?? l.forma ?? i}>
            <div className="mb-1 flex items-center justify-between gap-2 text-xs">
              <span className="truncate">{l.rotulo}</span>
              <span className="tabular shrink-0 text-muted-foreground">
                {numero(l.qtd)} · {moeda(l.valor)}
              </span>
            </div>
            <div className="h-1.5 w-full overflow-hidden rounded-full bg-muted">
              <div
                className={cn("h-full rounded-full transition-[width] duration-500")}
                style={{ width: `${Math.max(2, pct * 100)}%`, background: cor }}
              />
            </div>
          </li>
        );
      })}
    </ul>
  );
}

export function Distribuicoes({
  status,
  formas,
}: {
  status: Distribuicao[];
  formas: Distribuicao[];
}) {
  return (
    <Card className="h-full">
      <Tabs defaultValue="status">
        <CardHeader className="flex-row items-start justify-between gap-2">
          <div>
            <CardTitle>Pedidos do período</CardTitle>
            <CardDescription>Por status e por forma de pagamento</CardDescription>
          </div>
          <TabsList className="h-8">
            <TabsTrigger value="status" className="text-xs">
              Status
            </TabsTrigger>
            <TabsTrigger value="formas" className="text-xs">
              Pagamento
            </TabsTrigger>
          </TabsList>
        </CardHeader>
        <CardContent>
          <TabsContent value="status">
            <Barras linhas={status} chave="status" />
          </TabsContent>
          <TabsContent value="formas">
            <Barras linhas={formas} chave="forma" />
          </TabsContent>
        </CardContent>
      </Tabs>
    </Card>
  );
}
