import {
  AlertTriangle,
  ArrowUpRight,
  Boxes,
  CalendarDays,
  CheckSquare,
  Clock,
  PackageCheck,
  PackageX,
  Truck,
  Users,
  Wallet,
} from "lucide-react";

import { GraficoBarras } from "@/components/charts/GraficoBarras";
import { Vazio } from "@/components/estado";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { data as fmtData, moeda, numero, relativo } from "@/lib/formatos";
import { cn } from "@/lib/utils";

import type { Alertas, Atividade, EventoResumo, TarefaResumo, TopProduto } from "../types";

/* ---------------------------------------------------------------- Top produtos */
export function TopProdutos({ itens }: { itens: TopProduto[] }) {
  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>Produtos mais vendidos</CardTitle>
        <CardDescription>Unidades no período</CardDescription>
      </CardHeader>
      <CardContent>
        {itens.length === 0 ? (
          <Vazio titulo="Nenhum item vendido no período" className="py-8" />
        ) : (
          <GraficoBarras
            rotuloValor="Unidades"
            dados={itens.map((p) => ({ nome: p.nome, valor: p.qtd, detalhe: `Receita: ${moeda(p.receita)}` }))}
          />
        )}
      </CardContent>
    </Card>
  );
}

/* --------------------------------------------------------------------- Alertas */
interface Tile {
  rotulo: string;
  valor: number;
  icone: typeof Boxes;
  href: string;
  formato?: "moeda";
  /** Destaca quando > 0 (precisa de ação). */
  atencao?: boolean;
}

export function AlertasOperacionais({ alertas }: { alertas: Alertas }) {
  const tiles: Tile[] = [
    { rotulo: "Aguardando pagamento", valor: alertas.pedidos_aguardando, icone: Clock, href: "/pedidos?status=aguardando_pagamento", atencao: true },
    { rotulo: "Prontos p/ retirada", valor: alertas.pedidos_retirada, icone: PackageCheck, href: "/pedidos?status=pronto" },
    { rotulo: "Estoque baixo", valor: alertas.produtos_baixo, icone: AlertTriangle, href: "/produtos?situacao=baixo", atencao: true },
    { rotulo: "Esgotados", valor: alertas.produtos_esgotados, icone: PackageX, href: "/produtos?situacao=esgotado", atencao: true },
    { rotulo: "Tarefas atrasadas", valor: alertas.tarefas_atrasadas, icone: CheckSquare, href: "/tarefas/lista?atrasadas=true", atencao: true },
    { rotulo: "Valor em estoque", valor: alertas.valor_estoque, icone: Wallet, href: "/relatorios/estoque", formato: "moeda" },
    { rotulo: "Clientes", valor: alertas.clientes_total, icone: Users, href: "/clientes" },
    { rotulo: "Fornecedores ativos", valor: alertas.fornecedores_ativos, icone: Truck, href: "/fornecedores" },
  ];
  return (
    <div className="grid grid-cols-2 gap-3 md:grid-cols-4 xl:grid-cols-8">
      {tiles.map((t) => {
        const Icone = t.icone;
        const destacar = t.atencao && t.valor > 0;
        return (
          <a
            key={t.rotulo}
            href={t.href}
            className={cn(
              "group flex flex-col gap-1 rounded-xl border bg-card px-3 py-2.5 transition-colors hover:bg-accent",
              destacar && "border-warning/40",
            )}
          >
            <div className="flex items-center justify-between text-muted-foreground">
              <Icone className={cn("size-4", destacar && "text-warning")} />
              <ArrowUpRight className="size-3.5 opacity-0 transition-opacity group-hover:opacity-60" />
            </div>
            <div className="tabular font-display text-lg font-semibold leading-tight">
              {t.formato === "moeda" ? moeda(t.valor) : numero(t.valor)}
            </div>
            <div className="text-[11px] leading-tight text-muted-foreground">{t.rotulo}</div>
          </a>
        );
      })}
    </div>
  );
}

/* -------------------------------------------------------------- Minhas tarefas */
const COR_PRIORIDADE: Record<string, string> = {
  urgente: "bg-destructive/15 text-destructive",
  alta: "bg-warning/20 text-warning",
  normal: "bg-muted text-muted-foreground",
  baixa: "bg-muted text-muted-foreground",
};

export function MinhasTarefas({ tarefas }: { tarefas: TarefaResumo[] }) {
  return (
    <Card className="h-full">
      <CardHeader className="flex-row items-center justify-between">
        <div>
          <CardTitle>Minhas tarefas</CardTitle>
          <CardDescription>Abertas, por prazo</CardDescription>
        </div>
        <a href="/tarefas" className="text-xs text-muted-foreground hover:text-foreground">
          ver todas
        </a>
      </CardHeader>
      <CardContent>
        {tarefas.length === 0 ? (
          <Vazio icone={CheckSquare} titulo="Nada pendente" descricao="Nenhuma tarefa aberta atribuída a você." className="py-8" />
        ) : (
          <ul className="divide-y">
            {tarefas.map((t) => (
              <li key={t.id}>
                <a href={t.url} className="flex items-center gap-3 py-2 hover:bg-accent/50 -mx-2 px-2 rounded-md">
                  <div className="min-w-0 flex-1">
                    <div className="truncate text-sm">{t.titulo}</div>
                    <div className={cn("text-xs text-muted-foreground", t.atrasada && "text-destructive")}>
                      {t.prazo ? (t.atrasada ? `atrasada · ${fmtData(t.prazo)}` : fmtData(t.prazo)) : "sem prazo"}
                    </div>
                  </div>
                  <Badge variant="secondary" className={cn("font-normal", COR_PRIORIDADE[t.prioridade])}>
                    {t.prioridade_rotulo}
                  </Badge>
                </a>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}

/* ------------------------------------------------------------ Próximos eventos */
export function ProximosEventos({ eventos }: { eventos: EventoResumo[] }) {
  return (
    <Card className="h-full">
      <CardHeader className="flex-row items-center justify-between">
        <div>
          <CardTitle>Próximos eventos</CardTitle>
          <CardDescription>Em planejamento ou confirmados</CardDescription>
        </div>
        <a href="/eventos" className="text-xs text-muted-foreground hover:text-foreground">
          ver todos
        </a>
      </CardHeader>
      <CardContent>
        {eventos.length === 0 ? (
          <Vazio icone={CalendarDays} titulo="Nenhum evento à vista" className="py-8" />
        ) : (
          <ul className="divide-y">
            {eventos.map((e) => (
              <li key={e.id}>
                <a href={e.url || "/eventos/"} className="flex items-center gap-3 py-2 hover:bg-accent/50 -mx-2 px-2 rounded-md">
                  <div className="flex size-10 shrink-0 flex-col items-center justify-center rounded-lg bg-primary/10 leading-none">
                    <span className="tabular font-display text-base font-semibold">{fmtData(e.data, "dd")}</span>
                    <span className="text-[10px] uppercase text-muted-foreground">{fmtData(e.data, "MMM")}</span>
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="truncate text-sm">{e.nome}</div>
                    <div className="text-xs text-muted-foreground">
                      {e.tipo_rotulo} · {e.status_rotulo} · {numero(e.ingressos_vendidos)} ingressos
                    </div>
                  </div>
                  <div className="tabular text-sm text-muted-foreground">{moeda(e.receita_total)}</div>
                </a>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}

/* ------------------------------------------------------------------ Atividades */
export function AtividadesRecentes({ atividades }: { atividades: Atividade[] }) {
  return (
    <Card className="h-full">
      <CardHeader className="flex-row items-center justify-between">
        <div>
          <CardTitle>Atividades recentes</CardTitle>
          <CardDescription>O que a equipe fez por último</CardDescription>
        </div>
        <a href="/administracao/historico" className="text-xs text-muted-foreground hover:text-foreground">
          histórico
        </a>
      </CardHeader>
      <CardContent>
        {atividades.length === 0 ? (
          <Vazio icone={Clock} titulo="Sem atividades registradas ainda" className="py-8" />
        ) : (
          <ol className="scroll-suave max-h-80 space-y-3 overflow-y-auto pr-1">
            {atividades.map((a) => (
              <li key={a.id} className="flex gap-3 text-sm">
                <span className="mt-1.5 size-2 shrink-0 rounded-full bg-primary/70" />
                <div className="min-w-0 flex-1">
                  <div className="leading-snug">
                    <span className="font-medium">{a.usuario?.nome ?? "Sistema"}</span> {a.verbo}
                    {a.alvo && (
                      <>
                        {" "}
                        {a.url ? (
                          <a href={a.url} className="underline-offset-2 hover:underline">
                            {a.alvo}
                          </a>
                        ) : (
                          <span>{a.alvo}</span>
                        )}
                      </>
                    )}
                  </div>
                  {a.descricao && <div className="truncate text-xs text-muted-foreground">{a.descricao}</div>}
                  <div className="text-[11px] text-muted-foreground">{relativo(a.criado_em)}</div>
                </div>
              </li>
            ))}
          </ol>
        )}
      </CardContent>
    </Card>
  );
}
