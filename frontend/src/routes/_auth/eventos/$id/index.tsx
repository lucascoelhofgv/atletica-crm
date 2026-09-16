import { useMutation, useQueryClient, useSuspenseQuery } from "@tanstack/react-query";
import { createFileRoute, Link, useRouter } from "@tanstack/react-router";
import { CalendarDays, ExternalLink, MapPin, Pencil, UserRound, Users } from "lucide-react";
import { toast } from "sonner";

import { CabecalhoPagina } from "@/app/CabecalhoPagina";
import { GraficoBarras } from "@/components/charts/GraficoBarras";
import { ConfirmarExclusao } from "@/components/ConfirmarExclusao";
import { PaginaCarregando } from "@/components/estado";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { usePermissao } from "@/features/auth/queries";
import { chaves, eventoQuery, excluirEvento } from "@/features/eventos/api";
import { Custos, Lotes, Receitas } from "@/features/eventos/components/LinhasEvento";
import { data as fmtData, moeda, numero, percentual } from "@/lib/formatos";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/_auth/eventos/$id/")({
  loader: ({ context, params }) => context.queryClient.ensureQueryData(eventoQuery(Number(params.id))),
  pendingComponent: PaginaCarregando,
  component: PaginaEvento,
});

const COR_STATUS: Record<string, string> = {
  planejamento: "bg-muted text-muted-foreground",
  confirmado: "bg-primary/15 text-primary",
  realizado: "bg-success/15 text-success",
  cancelado: "bg-destructive/10 text-destructive",
};

function Kpi({ rotulo, valor, sub, tom }: { rotulo: string; valor: string; sub?: string; tom?: "bom" | "ruim" }) {
  return (
    <Card className="gap-1 py-4">
      <CardHeader className="px-4 pb-0"><CardDescription>{rotulo}</CardDescription>
        <CardTitle className={cn("tabular font-display text-2xl", tom === "bom" && "text-success", tom === "ruim" && "text-destructive")}>{valor}</CardTitle>
      </CardHeader>
      {sub && <CardContent className="px-4 text-xs text-muted-foreground">{sub}</CardContent>}
    </Card>
  );
}

function PaginaEvento() {
  const { id } = Route.useParams();
  const router = useRouter();
  const queryClient = useQueryClient();
  const permissao = usePermissao("eventos");
  const { data: e } = useSuspenseQuery(eventoQuery(Number(id)));
  const f = e.financeiro;

  const excluir = useMutation({
    mutationFn: () => excluirEvento(e.id),
    onSuccess: () => { void queryClient.invalidateQueries({ queryKey: chaves.todos }); toast.success("Evento excluído."); void router.navigate({ to: "/eventos", search: {} }); },
    onError: (erro: Error) => toast.error(erro.message),
  });

  const lucro = f.resultado > 0 ? "bom" : f.resultado < 0 ? "ruim" : undefined;
  const barras = [
    { nome: "Receita ingressos", valor: f.receita_ingressos },
    { nome: "Receitas extras", valor: f.receita_extra },
    { nome: "Custos", valor: f.custo_total },
  ];

  return (
    <div className="space-y-6">
      <CabecalhoPagina
        titulo={e.nome}
        voltar={{ para: "/eventos", rotulo: "Eventos" }}
        descricao={
          <span className="flex flex-wrap items-center gap-x-3 gap-y-1">
            <Badge variant="secondary" className={cn("font-normal", COR_STATUS[e.status])}>{e.status_rotulo}</Badge>
            <Badge variant="outline" className="font-normal">{e.tipo_rotulo}</Badge>
            <span className="flex items-center gap-1 text-xs text-muted-foreground"><CalendarDays className="size-3.5" /> {fmtData(e.data)}{e.horario && ` · ${e.horario}`}</span>
            {e.local && <span className="flex items-center gap-1 text-xs text-muted-foreground"><MapPin className="size-3.5" /> {e.local}</span>}
            {e.responsavel && <span className="flex items-center gap-1 text-xs text-muted-foreground"><UserRound className="size-3.5" /> {e.responsavel.nome}</span>}
            {e.link_inscricao && <a href={e.link_inscricao} target="_blank" rel="noreferrer" className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground"><ExternalLink className="size-3.5" /> ingressos</a>}
          </span>
        }
        acoes={
          permissao.escrever ? (
            <>
              <Button asChild size="sm" variant="outline"><Link to="/eventos/$id/editar" params={{ id }}><Pencil /> Editar</Link></Button>
              {permissao.excluir && <ConfirmarExclusao titulo={`Excluir ${e.nome}?`} descricao="Lotes, custos e receitas somem junto." aoConfirmar={() => excluir.mutateAsync()} pendente={excluir.isPending} />}
            </>
          ) : undefined
        }
      />

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <Kpi rotulo="Resultado" valor={moeda(f.resultado)} tom={lucro} sub={f.margem !== null ? `margem ${percentual(f.margem).replace("+", "")}` : "sem receita ainda"} />
        <Kpi rotulo="Receita total" valor={moeda(f.receita_total)} sub={`${moeda(f.receita_ingressos)} ingressos + ${moeda(f.receita_extra)} extras`} />
        <Kpi rotulo="Custos" valor={moeda(f.custo_total)} sub={`${moeda(f.custo_pago)} pagos · ${moeda(f.custo_a_pagar)} a pagar${f.orcamento_previsto ? ` · orçado ${moeda(f.orcamento_previsto)}` : ""}`} tom={f.orcamento_previsto && f.custo_total > f.orcamento_previsto ? "ruim" : undefined} />
        <Kpi rotulo="Público" valor={numero(f.publico_estimado)} sub={`${numero(f.ingressos_vendidos)} ingressos + ${numero(e.staff_cortesias)} staff${e.capacidade ? ` · cap. ${numero(e.capacidade)}` : ""}`} />
      </section>

      <section className="grid gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader><CardTitle>Receitas × custos</CardTitle><CardDescription>Onde entra e onde sai o dinheiro</CardDescription></CardHeader>
          <CardContent>
            <GraficoBarras dados={barras.map((b) => ({ nome: b.nome, valor: b.valor, detalhe: moeda(b.valor) }))} rotuloValor="R$" />
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle>Indicadores</CardTitle></CardHeader>
          <CardContent className="grid grid-cols-2 gap-3 text-sm">
            <div><div className="text-[11px] uppercase tracking-wide text-muted-foreground">Ticket médio</div><div className="tabular font-medium">{f.ticket_medio === null ? "—" : moeda(f.ticket_medio)}</div></div>
            <div><div className="text-[11px] uppercase tracking-wide text-muted-foreground">Custo por pessoa</div><div className="tabular font-medium">{f.custo_por_pessoa === null ? "—" : moeda(f.custo_por_pessoa)}</div></div>
            <div><div className="text-[11px] uppercase tracking-wide text-muted-foreground">Ponto de equilíbrio</div><div className="tabular font-medium">{f.breakeven_ingressos === null ? "—" : `${numero(f.breakeven_ingressos)} ingressos`}</div></div>
            <div><div className="text-[11px] uppercase tracking-wide text-muted-foreground">Previsto em ingressos</div><div className="tabular font-medium">{moeda(f.receita_ingressos_prevista)}</div></div>
            {e.publico_alvo && <div className="col-span-2"><div className="text-[11px] uppercase tracking-wide text-muted-foreground">Público-alvo</div><div className="flex items-center gap-1"><Users className="size-3.5 text-muted-foreground" /> {e.publico_alvo}</div></div>}
            {e.fornecedores.length > 0 && (
              <div className="col-span-2"><div className="text-[11px] uppercase tracking-wide text-muted-foreground">Fornecedores</div>
                <div className="flex flex-wrap gap-1 pt-1">{e.fornecedores.map((fo) => <Link key={fo.id} to="/fornecedores/$id" params={{ id: String(fo.id) }}><Badge variant="outline" className="font-normal hover:bg-accent">{fo.nome_exibicao}</Badge></Link>)}</div>
              </div>
            )}
            {(e.descricao || e.observacoes) && <p className="col-span-2 whitespace-pre-line text-xs text-muted-foreground">{e.descricao}{e.descricao && e.observacoes ? "\n" : ""}{e.observacoes}</p>}
          </CardContent>
        </Card>
      </section>

      <Lotes evento={e} podeEditar={permissao.escrever} />
      <Custos evento={e} podeEditar={permissao.escrever} />
      <Receitas evento={e} podeEditar={permissao.escrever} />
    </div>
  );
}
