import { useQuery } from "@tanstack/react-query";
import { createFileRoute, Link } from "@tanstack/react-router";
import { KanbanSquare, Plus } from "lucide-react";
import { z } from "zod";

import { CabecalhoPagina } from "@/app/CabecalhoPagina";
import { ErroCarregamento, SkeletonLinhas, Vazio } from "@/components/estado";
import { Paginacao } from "@/components/Paginacao";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { usePermissao } from "@/features/auth/queries";
import { opcoesTarefaQuery, tarefasQuery } from "@/features/tarefas/api";
import { COR_PRIORIDADE, COR_STATUS } from "@/features/tarefas/prioridade";
import { data as fmtData } from "@/lib/formatos";
import { cn } from "@/lib/utils";

const buscaSchema = z.object({
  status: z.string().optional().catch(undefined),
  prioridade: z.string().optional().catch(undefined),
  responsavel: z.number().optional().catch(undefined),
  minhas: z.boolean().optional().catch(undefined),
  atrasadas: z.boolean().optional().catch(undefined),
  pagina: z.number().optional().catch(undefined),
});

export const Route = createFileRoute("/_auth/tarefas/lista")({
  validateSearch: buscaSchema,
  component: PaginaLista,
});

const TODOS = "__todos__";

function PaginaLista() {
  const filtros = Route.useSearch();
  const navigate = Route.useNavigate();
  const permissao = usePermissao("tarefas");
  const consulta = useQuery(tarefasQuery(filtros));
  const { data: opcoes } = useQuery(opcoesTarefaQuery);
  const d = consulta.data;
  function definir(patch: Partial<typeof filtros>) {
    void navigate({ search: (ant) => ({ ...ant, ...patch }), replace: true });
  }

  return (
    <div className="space-y-4">
      <CabecalhoPagina
        titulo="Tarefas · lista"
        acoes={
          <>
            <Button asChild variant="outline" size="sm"><Link to="/tarefas" search={{}}><KanbanSquare /> Quadro</Link></Button>
            {permissao.escrever && <Button asChild size="sm"><Link to="/tarefas/nova"><Plus /> Nova tarefa</Link></Button>}
          </>
        }
      >
        <div className="flex flex-wrap items-center gap-3">
          <Select value={filtros.status ?? TODOS} onValueChange={(v) => definir({ status: v === TODOS ? undefined : v, pagina: undefined })}>
            <SelectTrigger size="sm" className="w-44"><SelectValue placeholder="Status" /></SelectTrigger>
            <SelectContent>
              <SelectItem value={TODOS}>Todos os status</SelectItem>
              {opcoes?.status.map((o) => <SelectItem key={o.valor} value={o.valor}>{o.rotulo}</SelectItem>)}
            </SelectContent>
          </Select>
          <Select value={filtros.prioridade ?? TODOS} onValueChange={(v) => definir({ prioridade: v === TODOS ? undefined : v, pagina: undefined })}>
            <SelectTrigger size="sm" className="w-44"><SelectValue placeholder="Prioridade" /></SelectTrigger>
            <SelectContent>
              <SelectItem value={TODOS}>Qualquer prioridade</SelectItem>
              {opcoes?.prioridades.map((o) => <SelectItem key={o.valor} value={o.valor}>{o.rotulo}</SelectItem>)}
            </SelectContent>
          </Select>
          <Select value={filtros.responsavel ? String(filtros.responsavel) : TODOS} onValueChange={(v) => definir({ responsavel: v === TODOS ? undefined : Number(v), pagina: undefined })}>
            <SelectTrigger size="sm" className="w-48"><SelectValue placeholder="Responsável" /></SelectTrigger>
            <SelectContent>
              <SelectItem value={TODOS}>Qualquer responsável</SelectItem>
              {opcoes?.membros.map((m) => <SelectItem key={m.id} value={String(m.id)}>{m.nome}</SelectItem>)}
            </SelectContent>
          </Select>
          <div className="flex items-center gap-2">
            <Switch id="minhas" checked={!!filtros.minhas} onCheckedChange={(v) => definir({ minhas: v || undefined, pagina: undefined })} />
            <Label htmlFor="minhas" className="cursor-pointer text-xs font-normal text-muted-foreground">Só as minhas</Label>
          </div>
          <div className="flex items-center gap-2">
            <Switch id="atrasadas" checked={!!filtros.atrasadas} onCheckedChange={(v) => definir({ atrasadas: v || undefined, pagina: undefined })} />
            <Label htmlFor="atrasadas" className="cursor-pointer text-xs font-normal text-muted-foreground">Só atrasadas</Label>
          </div>
        </div>
      </CabecalhoPagina>

      {consulta.isError && !d ? (
        <ErroCarregamento erro={consulta.error} tentarDeNovo={() => consulta.refetch()} />
      ) : !d ? (
        <SkeletonLinhas n={8} />
      ) : d.total === 0 ? (
        <Vazio titulo="Nenhuma tarefa" />
      ) : (
        <div className={cn("space-y-3 transition-opacity", consulta.isFetching && "opacity-70")}>
          <div className="overflow-hidden rounded-xl border bg-card">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Tarefa</TableHead>
                  <TableHead className="hidden md:table-cell">Responsável</TableHead>
                  <TableHead>Prazo</TableHead>
                  <TableHead className="hidden sm:table-cell">Prioridade</TableHead>
                  <TableHead>Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {d.resultados.map((t) => (
                  <TableRow key={t.id} className="cursor-pointer" onClick={() => void navigate({ to: "/tarefas/$id", params: { id: String(t.id) } })}>
                    <TableCell>
                      <Link to="/tarefas/$id" params={{ id: String(t.id) }} className="font-medium hover:underline" onClick={(e) => e.stopPropagation()}>{t.titulo}</Link>
                      {(t.cliente || t.pedido || t.fornecedor) && <div className="text-xs text-muted-foreground">{t.cliente?.nome ?? t.pedido?.nome ?? t.fornecedor?.nome}</div>}
                    </TableCell>
                    <TableCell className="hidden text-muted-foreground md:table-cell">{t.responsavel?.nome ?? "—"}</TableCell>
                    <TableCell className={cn(t.atrasada && "font-medium text-destructive")}>{t.prazo ? fmtData(t.prazo) : "—"}</TableCell>
                    <TableCell className="hidden sm:table-cell"><Badge variant="secondary" className={cn("font-normal", COR_PRIORIDADE[t.prioridade])}>{t.prioridade_rotulo}</Badge></TableCell>
                    <TableCell><Badge variant="secondary" className={cn("font-normal", COR_STATUS[t.status])}>{t.status_rotulo}</Badge></TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
          <Paginacao pagina={d.pagina} paginas={d.paginas} total={d.total} rotulo="tarefas" aoMudar={(p) => definir({ pagina: p === 1 ? undefined : p })} />
        </div>
      )}
    </div>
  );
}
