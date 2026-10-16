import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { createFileRoute, Link } from "@tanstack/react-router";
import { format, parseISO } from "date-fns";
import { ptBR } from "date-fns/locale";
import { AlertTriangle, LoaderCircle, RefreshCw, Trophy } from "lucide-react";
import { useState } from "react";
import { Bar, BarChart, CartesianGrid, Legend, Tooltip, XAxis, YAxis } from "recharts";
import { toast } from "sonner";

import { CabecalhoPagina } from "@/app/CabecalhoPagina";
import { DOMINIO_NAO_NEGATIVO, tickMoeda } from "@/components/charts/chart-utils";
import { ErroCarregamento, PaginaCarregando, Vazio } from "@/components/estado";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ChartContainer, type ChartConfig } from "@/components/ui/chart";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { useUsuario } from "@/features/auth/queries";
import { DESTINOS_ESPORTES, fontesQuery, resumoEsportesQuery, sincronizarFonte } from "@/features/esportes/api";
import type { LinhaModalidade, MesEsportes, ResumoEsportes } from "@/features/esportes/types";
import { data as fmtData, moeda, numero, relativo } from "@/lib/formatos";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/_auth/esportes/")({
  component: PaginaEsportes,
});

const pctFmt = new Intl.NumberFormat("pt-BR", { style: "percent", maximumFractionDigits: 0 });
const pct = (v: number | null) => (v === null ? "sem orçamento" : pctFmt.format(v));
/** Valor unitário sem centavos quando não tem: "R$ 200", "R$ 86,5". */
const unitFmt = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL", minimumFractionDigits: 0, maximumFractionDigits: 2 });
const unit = (v: number) => unitFmt.format(Number(v));

function Tile({ rotulo, valor, detalhe }: { rotulo: string; valor: string; detalhe?: React.ReactNode }) {
  return (
    <Card className="gap-1 py-4">
      <CardHeader className="px-4 pb-0">
        <CardDescription>{rotulo}</CardDescription>
        <CardTitle className="tabular font-display text-2xl">{valor}</CardTitle>
      </CardHeader>
      {detalhe && <CardContent className="px-4 text-xs text-muted-foreground">{detalhe}</CardContent>}
    </Card>
  );
}

/** Sincroniza as fontes de Esportes cadastradas, uma depois da outra. */
function BotaoSincronizar() {
  const queryClient = useQueryClient();
  const fontes = useQuery(fontesQuery);
  const deEsportes = (fontes.data ?? []).filter((f) => DESTINOS_ESPORTES.includes(f.destino));

  const sincronizar = useMutation({
    mutationFn: async () => {
      const resultados = [];
      for (const f of deEsportes) resultados.push(await sincronizarFonte(f.id));
      return resultados;
    },
    onSuccess: (resultados) => {
      for (const r of resultados) {
        const avisos = r.avisos.length;
        toast.success(`${r.fonte.nome}: ${r.resumo}`, {
          description: avisos ? "Os avisos estão em Administração › Fontes de planilha." : undefined,
        });
      }
    },
    onError: (e: Error) => toast.error(e.message),
    onSettled: () => {
      void queryClient.invalidateQueries({ queryKey: ["esportes"] });
      void queryClient.invalidateQueries({ queryKey: ["integracoes", "fontes"] });
    },
  });

  if (fontes.isPending) return null;
  if (!deEsportes.length) {
    return (
      <Button asChild variant="outline" size="sm">
        <Link to="/administracao/fontes">Cadastrar as planilhas</Link>
      </Button>
    );
  }
  return (
    <Button size="sm" onClick={() => sincronizar.mutate()} disabled={sincronizar.isPending}>
      {sincronizar.isPending ? <LoaderCircle className="animate-spin" /> : <RefreshCw />}
      {sincronizar.isPending ? "Lendo as planilhas…" : "Sincronizar planilhas"}
    </Button>
  );
}

/** Uma linha por modalidade: trilho = orçado, preenchimento = gasto. */
function OrcadoRealizado({ linhas }: { linhas: LinhaModalidade[] }) {
  return (
    <ul className="space-y-3.5">
      {linhas.map((l) => {
        const acima = l.tem_orcamento && l.realizado > l.orcado;
        const largura = l.orcado > 0 ? Math.min(100, (l.realizado / l.orcado) * 100) : l.realizado > 0 ? 100 : 0;
        return (
          <li key={l.id} title={`${l.nome}: ${moeda(l.realizado)} gastos de ${moeda(l.orcado)} orçados`}>
            <div className="mb-1 flex flex-wrap items-baseline justify-between gap-x-3 text-sm">
              <span className="font-medium">{l.nome}</span>
              <span className="tabular text-xs text-muted-foreground">
                <span className="font-medium text-foreground">{moeda(l.realizado)}</span>
                {l.tem_orcamento ? ` de ${moeda(l.orcado)} · ${pct(l.uso)}` : " · sem orçamento"}
              </span>
            </div>
            <div className="h-2.5 overflow-hidden rounded-full bg-muted">
              <div
                className={cn("h-full rounded-full", acima ? "bg-destructive" : "bg-[var(--esportes-tecnico)]")}
                style={{ width: `${largura}%` }}
              />
            </div>
            <div className="mt-1 flex flex-wrap gap-1.5 text-xs text-muted-foreground">
              {!l.tem_registros && <Badge variant="outline" className="font-normal">sem treinos lançados</Badge>}
              {acima && (
                <Badge variant="secondary" className="gap-1 bg-destructive/10 font-normal text-destructive">
                  <AlertTriangle className="size-3" /> acima do orçado em {moeda(l.realizado - l.orcado)}
                </Badge>
              )}
            </div>
          </li>
        );
      })}
    </ul>
  );
}

const configMes: ChartConfig = {
  quadra: { label: "Quadra", color: "var(--esportes-quadra)" },
  tecnico: { label: "Técnico", color: "var(--esportes-tecnico)" },
};

function TooltipMes({ active, payload }: { active?: boolean; payload?: ReadonlyArray<{ payload?: MesEsportes }> }) {
  const p = payload?.[0]?.payload;
  if (!active || !p) return null;
  return (
    <div className="rounded-lg border bg-popover px-3 py-2 text-xs shadow-md">
      <div className="mb-1 font-medium capitalize">{format(parseISO(`${p.mes}-01`), "MMMM 'de' yyyy", { locale: ptBR })}</div>
      {(["tecnico", "quadra"] as const).map((k) => (
        <div key={k} className="flex items-center justify-between gap-6">
          <span className="flex items-center gap-1.5 text-muted-foreground">
            <span className="size-2 rounded-full" style={{ background: configMes[k].color }} />
            {configMes[k].label}
          </span>
          <span className="tabular font-medium">{moeda(p[k])}</span>
        </div>
      ))}
      <div className="mt-1 flex justify-between gap-6 border-t pt-1">
        <span className="text-muted-foreground">Total</span>
        <span className="tabular font-medium">{moeda(p.realizado)}</span>
      </div>
      <div className="text-muted-foreground">
        {numero(p.treinos)} treino(s) confirmado(s), {numero(p.jogos)} jogo(s)
      </div>
    </div>
  );
}

function GastoPorMes({ meses }: { meses: MesEsportes[] }) {
  const dados = meses.map((m) => ({ ...m, rotulo: format(parseISO(`${m.mes}-01`), "MMM", { locale: ptBR }) }));
  return (
    <ChartContainer config={configMes} className="aspect-auto h-72 w-full">
      <BarChart data={dados} margin={{ top: 8, right: 8, left: 4, bottom: 0 }} barCategoryGap="28%">
        <CartesianGrid vertical={false} strokeOpacity={0.4} />
        <XAxis dataKey="rotulo" tickLine={false} axisLine={false} tick={{ fontSize: 12 }} />
        <YAxis tickFormatter={tickMoeda} domain={DOMINIO_NAO_NEGATIVO} tickLine={false} axisLine={false} width={64} tick={{ fontSize: 12 }} />
        <Tooltip cursor={{ fill: "var(--accent)", opacity: 0.4 }} content={<TooltipMes />} />
        <Legend verticalAlign="top" align="right" height={28} iconType="circle" iconSize={8} wrapperStyle={{ fontSize: 12 }} />
        <Bar dataKey="quadra" name="Quadra" stackId="g" fill="var(--color-quadra)" stroke="var(--card)" strokeWidth={2} />
        <Bar dataKey="tecnico" name="Técnico" stackId="g" fill="var(--color-tecnico)" stroke="var(--card)" strokeWidth={2} radius={[4, 4, 0, 0]} />
      </BarChart>
    </ChartContainer>
  );
}

function valorUnitario(orcado: number | null, real: number | null) {
  if (orcado === null && real === null) return <span className="text-muted-foreground">sem dado</span>;
  const diferente = orcado !== null && real !== null && Number(orcado) !== Number(real);
  return (
    <span className="tabular whitespace-nowrap">
      {orcado !== null ? unit(orcado) : "?"}
      {real !== null && (
        <>
          {" "}
          <span className="text-muted-foreground">→</span>{" "}
          <span className={cn(diferente && "font-medium text-foreground")}>{unit(real)}</span>
        </>
      )}
    </span>
  );
}

function TabelaModalidades({ linhas }: { linhas: LinhaModalidade[] }) {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Modalidade</TableHead>
          <TableHead className="text-right">Treinos</TableHead>
          <TableHead className="text-right">Cancelados</TableHead>
          <TableHead className="text-right">Jogos</TableHead>
          <TableHead>Quadra</TableHead>
          <TableHead>Técnico</TableHead>
          <TableHead className="text-right">Orçado</TableHead>
          <TableHead className="text-right">Gasto</TableHead>
          <TableHead className="text-right">Sobra</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {linhas.map((l) => (
          <TableRow key={l.id}>
            <TableCell className="min-w-36 max-w-48 whitespace-normal">
              <div className="font-medium">{l.nome}</div>
              <div className="text-xs text-muted-foreground">{[l.dia_semana, l.local].filter(Boolean).join(" · ")}</div>
            </TableCell>
            <TableCell className="tabular text-right">
              {numero(l.treinos_confirmados)}
              <span className="text-muted-foreground"> / {numero(l.treinos_previstos)}</span>
            </TableCell>
            <TableCell className="tabular text-right">{numero(l.treinos_cancelados)}</TableCell>
            <TableCell className="tabular text-right">
              {numero(l.jogos_registrados)}
              <span className="text-muted-foreground"> / {numero(l.jogos_previstos)}</span>
            </TableCell>
            <TableCell>{valorUnitario(l.valor_quadra_orcado, l.valor_quadra_real)}</TableCell>
            <TableCell>{valorUnitario(l.valor_tecnico_orcado, l.valor_tecnico_real)}</TableCell>
            <TableCell className="tabular text-right">{moeda(l.orcado)}</TableCell>
            <TableCell className="tabular text-right">{moeda(l.realizado)}</TableCell>
            <TableCell className={cn("tabular text-right", l.diferenca < 0 && "text-destructive")}>{moeda(l.diferenca)}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

function Conteudo({ r }: { r: ResumoEsportes }) {
  const t = r.totais;
  const semRegistros = t.treinos_registrados === 0 && t.jogos_registrados === 0;
  return (
    <>
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <Tile rotulo="Orçado no semestre" valor={moeda(t.orcado)} detalhe={`${numero(r.modalidades.filter((m) => m.tem_orcamento).length)} modalidade(s)`} />
        <Tile rotulo="Gasto registrado" valor={moeda(t.realizado)} detalhe={t.uso === null ? "sem orçamento" : `${pct(t.uso)} do orçado`} />
        <Tile
          rotulo="Treinos confirmados"
          valor={numero(t.treinos_confirmados)}
          detalhe={`de ${numero(t.treinos_previstos)} previstos · ${numero(t.jogos_registrados)} jogo(s)`}
        />
        <Tile rotulo="Treinos cancelados" valor={numero(t.treinos_cancelados)} detalhe="marcados como não confirmados" />
      </div>

      {semRegistros && (
        <Vazio
          icone={Trophy}
          titulo="Nenhum treino lançado neste semestre"
          descricao="O orçamento já está aqui. Os gastos aparecem quando a planilha de treinos deste semestre for cadastrada em Fontes de planilha e sincronizada."
        />
      )}

      <div className="grid gap-4 lg:grid-cols-5">
        <Card className="lg:col-span-3">
          <CardHeader>
            <CardTitle>Orçado x gasto por modalidade</CardTitle>
            <CardDescription>A barra cheia é o orçamento do semestre; a parte pintada é o que já foi gasto.</CardDescription>
          </CardHeader>
          <CardContent>
            <OrcadoRealizado linhas={r.modalidades} />
          </CardContent>
        </Card>
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Gasto por mês</CardTitle>
            <CardDescription>Técnico e quadra que de fato foram usados.</CardDescription>
          </CardHeader>
          <CardContent>
            <GastoPorMes meses={r.por_mes} />
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Detalhe por modalidade</CardTitle>
          <CardDescription>
            Treinos e jogos: confirmados / previstos no orçamento. Quadra e técnico: valor do orçamento → valor que a
            planilha de treinos usa.
          </CardDescription>
        </CardHeader>
        <CardContent className="overflow-x-auto">
          <TabelaModalidades linhas={r.modalidades} />
        </CardContent>
      </Card>
    </>
  );
}

function PaginaEsportes() {
  const usuario = useUsuario();
  const [escolha, setEscolha] = useState<{ ano: number; semestre: number } | null>(null);
  const consulta = useQuery(resumoEsportesQuery(escolha?.ano, escolha?.semestre));
  const r = consulta.data;

  if (consulta.isError && !r) return <ErroCarregamento erro={consulta.error} tentarDeNovo={() => consulta.refetch()} />;
  if (!r) return <PaginaCarregando />;

  const valorSelect = `${r.ano}.${r.semestre}`;
  const opcoes = r.semestres_disponiveis.length ? r.semestres_disponiveis : [{ ano: r.ano, semestre: r.semestre }];
  const periodo =
    r.primeiro_registro && r.ultimo_registro
      ? `treinos de ${fmtData(r.primeiro_registro)} a ${fmtData(r.ultimo_registro)}`
      : "sem treinos lançados";

  return (
    <div className="mx-auto max-w-6xl space-y-4">
      <CabecalhoPagina
        titulo="Esportes"
        descricao={
          <>
            Orçado x gasto por modalidade, lido das planilhas da diretoria de Esportes · {periodo}
            {r.ultima_sincronizacao && <> · sincronizado {relativo(r.ultima_sincronizacao)}</>}
          </>
        }
        acoes={
          <>
            <Select
              value={valorSelect}
              onValueChange={(v) => {
                const [ano, semestre] = v.split(".").map(Number);
                setEscolha({ ano, semestre });
              }}
            >
              <SelectTrigger size="sm" className="w-auto" aria-label="Semestre">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {opcoes.map((o) => (
                  <SelectItem key={`${o.ano}.${o.semestre}`} value={`${o.ano}.${o.semestre}`}>
                    Semestre {o.ano}.{o.semestre}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {usuario.eh_admin && <BotaoSincronizar />}
          </>
        }
      />

      {r.modalidades.length === 0 ? (
        <Vazio
          icone={Trophy}
          titulo="Nada de Esportes ainda"
          descricao="Cadastre as planilhas de orçamento e de treinos em Administração › Fontes de planilha e clique em Sincronizar."
          acao={
            usuario.eh_admin ? (
              <Button asChild size="sm">
                <Link to="/administracao/fontes">Ir para Fontes de planilha</Link>
              </Button>
            ) : undefined
          }
        />
      ) : (
        <Conteudo r={r} />
      )}
    </div>
  );
}
