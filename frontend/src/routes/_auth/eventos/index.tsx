import { useQuery } from "@tanstack/react-query";
import { createFileRoute, Link } from "@tanstack/react-router";
import { Plus, Search, X } from "lucide-react";
import { useEffect, useState } from "react";
import { z } from "zod";

import { CabecalhoPagina } from "@/app/CabecalhoPagina";
import { ErroCarregamento, SkeletonLinhas, Vazio } from "@/components/estado";
import { Paginacao } from "@/components/Paginacao";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { usePermissao } from "@/features/auth/queries";
import { eventosQuery, opcoesEventoQuery } from "@/features/eventos/api";
import { data as fmtData, moeda, numero, percentual } from "@/lib/formatos";
import { cn } from "@/lib/utils";

const buscaSchema = z.object({
  q: z.string().optional().catch(undefined),
  tipo: z.string().optional().catch(undefined),
  status: z.string().optional().catch(undefined),
  futuros: z.boolean().optional().catch(undefined),
  pagina: z.number().optional().catch(undefined),
});

export const Route = createFileRoute("/_auth/eventos/")({
  validateSearch: buscaSchema,
  component: PaginaEventos,
});

const TODOS = "__todos__";
const COR_STATUS_EVENTO: Record<string, string> = {
  planejamento: "bg-muted text-muted-foreground",
  confirmado: "bg-primary/15 text-primary",
  realizado: "bg-success/15 text-success",
  cancelado: "bg-destructive/10 text-destructive",
};

function PaginaEventos() {
  const filtros = Route.useSearch();
  const navigate = Route.useNavigate();
  const permissao = usePermissao("eventos");
  const consulta = useQuery(eventosQuery(filtros));
  const { data: opcoes } = useQuery(opcoesEventoQuery);
  const d = consulta.data;

  const [termo, setTermo] = useState(filtros.q ?? "");
  useEffect(() => {
    const t = window.setTimeout(() => {
      if ((filtros.q ?? "") !== termo) definir({ q: termo || undefined, pagina: undefined });
    }, 300);
    return () => window.clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [termo]);
  function definir(patch: Partial<typeof filtros>) {
    void navigate({ search: (ant) => ({ ...ant, ...patch }), replace: true });
  }
  const temFiltro = !!(filtros.q || filtros.tipo || filtros.status || filtros.futuros);

  return (
    <div className="space-y-4">
      <CabecalhoPagina
        titulo="Eventos e festas"
        descricao="Ingressos, custos, receitas e o resultado de cada evento."
        acoes={permissao.escrever ? <Button asChild size="sm"><Link to="/eventos/novo"><Plus /> Novo evento</Link></Button> : undefined}
      >
        <div className="flex flex-wrap items-center gap-3">
          <div className="relative w-full max-w-xs">
            <Search className="pointer-events-none absolute left-2.5 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
            <Input placeholder="Nome ou local…" className="h-8 pl-8 pr-8" value={termo} onChange={(e) => setTermo(e.target.value)} />
            {termo && <button type="button" onClick={() => setTermo("")} className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground" aria-label="Limpar busca"><X className="size-4" /></button>}
          </div>
          <Select value={filtros.tipo ?? TODOS} onValueChange={(v) => definir({ tipo: v === TODOS ? undefined : v, pagina: undefined })}>
            <SelectTrigger size="sm" className="w-48"><SelectValue placeholder="Tipo" /></SelectTrigger>
            <SelectContent>
              <SelectItem value={TODOS}>Todos os tipos</SelectItem>
              {opcoes?.tipos.map((o) => <SelectItem key={o.valor} value={o.valor}>{o.rotulo}</SelectItem>)}
            </SelectContent>
          </Select>
          <Select value={filtros.status ?? TODOS} onValueChange={(v) => definir({ status: v === TODOS ? undefined : v, pagina: undefined })}>
            <SelectTrigger size="sm" className="w-44"><SelectValue placeholder="Status" /></SelectTrigger>
            <SelectContent>
              <SelectItem value={TODOS}>Todos os status</SelectItem>
              {opcoes?.status.map((o) => <SelectItem key={o.valor} value={o.valor}>{o.rotulo}</SelectItem>)}
            </SelectContent>
          </Select>
          <div className="flex items-center gap-2">
            <Switch id="futuros" checked={!!filtros.futuros} onCheckedChange={(v) => definir({ futuros: v || undefined, pagina: undefined })} />
            <Label htmlFor="futuros" className="cursor-pointer text-xs font-normal text-muted-foreground">Só os próximos</Label>
          </div>
          {temFiltro && <Button variant="ghost" size="sm" onClick={() => { setTermo(""); void navigate({ search: {}, replace: true }); }}>Limpar filtros</Button>}
        </div>
      </CabecalhoPagina>

      {consulta.isError && !d ? (
        <ErroCarregamento erro={consulta.error} tentarDeNovo={() => consulta.refetch()} />
      ) : !d ? (
        <SkeletonLinhas n={6} />
      ) : d.total === 0 ? (
        <Vazio titulo={temFiltro ? "Nenhum evento com esses filtros" : "Nenhum evento cadastrado"}
          acao={permissao.escrever && !temFiltro ? <Button asChild size="sm"><Link to="/eventos/novo"><Plus /> Novo evento</Link></Button> : undefined} />
      ) : (
        <div className={cn("space-y-3 transition-opacity", consulta.isFetching && "opacity-70")}>
          <div className="overflow-hidden rounded-xl border bg-card">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Evento</TableHead>
                  <TableHead>Data</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="hidden text-right md:table-cell">Ingressos</TableHead>
                  <TableHead className="hidden text-right lg:table-cell">Receita</TableHead>
                  <TableHead className="hidden text-right lg:table-cell">Custos</TableHead>
                  <TableHead className="text-right">Resultado</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {d.resultados.map((e) => {
                  const f = e.financeiro;
                  return (
                    <TableRow key={e.id} className="cursor-pointer" onClick={() => void navigate({ to: "/eventos/$id", params: { id: String(e.id) } })}>
                      <TableCell>
                        <Link to="/eventos/$id" params={{ id: String(e.id) }} className="font-medium hover:underline" onClick={(ev) => ev.stopPropagation()}>{e.nome}</Link>
                        <div className="text-xs text-muted-foreground">{e.tipo_rotulo}{e.local && ` · ${e.local}`}</div>
                      </TableCell>
                      <TableCell className="text-muted-foreground">{fmtData(e.data)}</TableCell>
                      <TableCell><Badge variant="secondary" className={cn("font-normal", COR_STATUS_EVENTO[e.status])}>{e.status_rotulo}</Badge></TableCell>
                      <TableCell className="tabular hidden text-right md:table-cell">{numero(f.ingressos_vendidos)}<span className="text-xs text-muted-foreground">/{numero(f.ingressos_previstos)}</span></TableCell>
                      <TableCell className="tabular hidden text-right lg:table-cell">{moeda(f.receita_total)}</TableCell>
                      <TableCell className="tabular hidden text-right text-muted-foreground lg:table-cell">{moeda(f.custo_total)}</TableCell>
                      <TableCell className={cn("tabular text-right font-medium", f.resultado > 0 ? "text-success" : f.resultado < 0 ? "text-destructive" : "")}>
                        {moeda(f.resultado)}
                        {f.margem !== null && <span className="ml-1 text-xs font-normal text-muted-foreground">{percentual(f.margem).replace("+", "")}</span>}
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </div>
          <Paginacao pagina={d.pagina} paginas={d.paginas} total={d.total} rotulo="eventos" aoMudar={(p) => definir({ pagina: p === 1 ? undefined : p })} />
        </div>
      )}
    </div>
  );
}
