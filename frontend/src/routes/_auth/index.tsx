import { useQuery } from "@tanstack/react-query";
import { createFileRoute } from "@tanstack/react-router";
import { LoaderCircle } from "lucide-react";

import { GraficoSerie } from "@/components/charts/GraficoSerie";
import { ErroCarregamento, SkeletonCard } from "@/components/estado";
import { PeriodoControle } from "@/components/periodo/PeriodoControle";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useUsuario } from "@/features/auth/queries";
import { dashboardQuery } from "@/features/dashboard/api";
import { Distribuicoes } from "@/features/dashboard/components/Distribuicoes";
import { KpiCard } from "@/features/dashboard/components/KpiCard";
import {
  AlertasOperacionais,
  AtividadesRecentes,
  MinhasTarefas,
  ProximosEventos,
  TopProdutos,
} from "@/features/dashboard/components/Paineis";
import { data as fmtData } from "@/lib/formatos";
import { usePeriodo } from "@/lib/periodo";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/_auth/")({
  component: PaginaPainel,
});

function saudacao() {
  const hora = new Date().getHours();
  if (hora < 12) return "Bom dia";
  if (hora < 18) return "Boa tarde";
  return "Boa noite";
}

function Esqueleto() {
  return (
    <div className="space-y-6" aria-busy="true">
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <SkeletonCard key={i} linhas={1} />
        ))}
      </div>
      <div className="grid gap-4 lg:grid-cols-3">
        <Skeleton className="h-72 lg:col-span-2" />
        <Skeleton className="h-72" />
      </div>
    </div>
  );
}

function PaginaPainel() {
  const usuario = useUsuario();
  const { valores } = usePeriodo();
  const consulta = useQuery(dashboardQuery(valores));
  const d = consulta.data;
  const primeiroNome = usuario.nome.split(" ")[0];
  const comparar = valores.comparar;

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <h1 className="font-display text-2xl font-semibold tracking-tight">
            {saudacao()}, {primeiroNome}
          </h1>
          <p className="text-sm text-muted-foreground">
            {d ? (
              <>
                <span>{d.periodo.rotulo}</span>
                <span className="text-muted-foreground/60">
                  {" · "}
                  {fmtData(d.periodo.inicio)} a {fmtData(d.periodo.fim)}
                </span>
                {comparar && (
                  <span className="text-muted-foreground/60">
                    {" · "}vs {fmtData(d.periodo.anterior.inicio)} a {fmtData(d.periodo.anterior.fim)}
                  </span>
                )}
              </>
            ) : (
              "Carregando o período…"
            )}
            {consulta.isFetching && d && (
              <LoaderCircle
                className="ml-2 inline size-3.5 animate-spin align-[-2px] text-muted-foreground/60"
                aria-label="atualizando"
              />
            )}
          </p>
        </div>
        <PeriodoControle />
      </div>

      {consulta.isError && !d ? (
        <ErroCarregamento erro={consulta.error} tentarDeNovo={() => consulta.refetch()} />
      ) : !d ? (
        <Esqueleto />
      ) : (
        <div className={cn("space-y-6 transition-opacity", consulta.isFetching && "opacity-70")}>
          <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <KpiCard id="receita" rotulo="Receita" kpi={d.kpis.receita} formato="moeda" comparar={comparar} indice={0} />
            <KpiCard id="pedidos" rotulo="Pedidos" kpi={d.kpis.pedidos} comparar={comparar} indice={1} />
            <KpiCard id="clientes" rotulo="Clientes novos" kpi={d.kpis.clientes_novos} comparar={comparar} indice={2} />
            <KpiCard id="ticket" rotulo="Ticket médio" kpi={d.kpis.ticket_medio} formato="moeda" comparar={comparar} indice={3} />
          </section>

          <section className="grid gap-4 lg:grid-cols-3">
            <Card className="lg:col-span-2">
              <CardHeader>
                <CardTitle>Receita</CardTitle>
                <CardDescription>
                  Pedidos pagos, em separação, prontos ou entregues, por{" "}
                  {d.periodo.granularidade === "mes" ? "mês" : "dia"}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <GraficoSerie
                  dados={d.series.receita}
                  granularidade={d.periodo.granularidade}
                  rotulo="Receita"
                  formato="moeda"
                  comparar={comparar}
                />
              </CardContent>
            </Card>
            <Distribuicoes status={d.status_pedidos} formas={d.formas_pagamento} />
          </section>

          <section className="grid gap-4 lg:grid-cols-3">
            <Card className="lg:col-span-2">
              <CardHeader>
                <CardTitle>Pedidos</CardTitle>
                <CardDescription>
                  Quantidade por {d.periodo.granularidade === "mes" ? "mês" : "dia"} (sem rascunhos e cancelados)
                </CardDescription>
              </CardHeader>
              <CardContent>
                <GraficoSerie
                  dados={d.series.pedidos}
                  granularidade={d.periodo.granularidade}
                  rotulo="Pedidos"
                  tipo="barras"
                  comparar={comparar}
                  cor="var(--chart-2)"
                />
              </CardContent>
            </Card>
            <TopProdutos itens={d.top_produtos} />
          </section>

          <section className="space-y-2">
            <h2 className="px-1 text-sm font-medium text-muted-foreground">Situação agora</h2>
            <AlertasOperacionais alertas={d.alertas} />
          </section>

          <section className="grid gap-4 lg:grid-cols-3">
            <MinhasTarefas tarefas={d.minhas_tarefas} />
            <ProximosEventos eventos={d.proximos_eventos} />
            <AtividadesRecentes atividades={d.atividades} />
          </section>
        </div>
      )}
    </div>
  );
}
