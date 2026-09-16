import { useQuery } from "@tanstack/react-query";
import { createFileRoute, Link } from "@tanstack/react-router";
import { ArrowDownRight, ArrowUpRight } from "lucide-react";
import { z } from "zod";

import { CabecalhoPagina } from "@/app/CabecalhoPagina";
import { ErroCarregamento, SkeletonLinhas, Vazio } from "@/components/estado";
import { Paginacao } from "@/components/Paginacao";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { movimentacoesQuery, opcoesProdutoQuery } from "@/features/produtos/api";
import { dataHora, numero } from "@/lib/formatos";
import { cn } from "@/lib/utils";

const buscaSchema = z.object({
  produto: z.number().optional().catch(undefined),
  tipo: z.string().optional().catch(undefined),
  pagina: z.number().optional().catch(undefined),
});

export const Route = createFileRoute("/_auth/produtos/movimentacoes")({
  validateSearch: buscaSchema,
  component: PaginaMovimentacoes,
});

const TODOS = "__todos__";

function PaginaMovimentacoes() {
  const filtros = Route.useSearch();
  const navigate = Route.useNavigate();
  const consulta = useQuery(movimentacoesQuery(filtros));
  const { data: opcoes } = useQuery(opcoesProdutoQuery);
  const d = consulta.data;

  function definir(patch: Partial<typeof filtros>) {
    void navigate({ search: (ant) => ({ ...ant, ...patch }), replace: true });
  }

  return (
    <div className="space-y-4">
      <CabecalhoPagina
        titulo="Movimentações de estoque"
        descricao="Toda entrada e saída, com quem fez e o saldo resultante."
        voltar={{ para: "/produtos", rotulo: "Produtos" }}
      >
        <div className="flex flex-wrap items-center gap-3">
          <Select value={filtros.tipo ?? TODOS} onValueChange={(v) => definir({ tipo: v === TODOS ? undefined : v, pagina: undefined })}>
            <SelectTrigger size="sm" className="w-56"><SelectValue placeholder="Tipo" /></SelectTrigger>
            <SelectContent>
              <SelectItem value={TODOS}>Todos os tipos</SelectItem>
              {opcoes?.tipos_movimentacao.map((o) => <SelectItem key={o.valor} value={o.valor}>{o.rotulo}</SelectItem>)}
            </SelectContent>
          </Select>
          {filtros.produto && (
            <button type="button" className="text-xs text-muted-foreground underline-offset-2 hover:underline" onClick={() => definir({ produto: undefined, pagina: undefined })}>
              Filtrando por um produto · ver todos
            </button>
          )}
        </div>
      </CabecalhoPagina>

      {consulta.isError && !d ? (
        <ErroCarregamento erro={consulta.error} tentarDeNovo={() => consulta.refetch()} />
      ) : !d ? (
        <SkeletonLinhas n={10} />
      ) : d.total === 0 ? (
        <Vazio titulo="Nenhuma movimentação" />
      ) : (
        <div className={cn("space-y-3 transition-opacity", consulta.isFetching && "opacity-70")}>
          <div className="overflow-hidden rounded-xl border bg-card">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Quando</TableHead>
                  <TableHead>Produto</TableHead>
                  <TableHead>Tipo</TableHead>
                  <TableHead className="text-right">Qtd.</TableHead>
                  <TableHead className="text-right">Saldo após</TableHead>
                  <TableHead className="hidden md:table-cell">Motivo</TableHead>
                  <TableHead className="hidden lg:table-cell">Quem</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {d.resultados.map((m) => (
                  <TableRow key={m.id}>
                    <TableCell className="text-muted-foreground">{dataHora(m.data)}</TableCell>
                    <TableCell>
                      <Link to="/produtos/$id" params={{ id: String(m.produto) }} className="font-medium hover:underline">{m.produto_nome}</Link>
                    </TableCell>
                    <TableCell>
                      <span className="flex items-center gap-1.5">
                        {m.eh_entrada ? <ArrowUpRight className="size-3.5 text-success" /> : <ArrowDownRight className="size-3.5 text-destructive" />}
                        {m.tipo_rotulo}
                        {m.pedido_numero && <span className="text-xs text-muted-foreground">· {m.pedido_numero}</span>}
                      </span>
                    </TableCell>
                    <TableCell className={cn("tabular text-right font-medium", m.eh_entrada ? "text-success" : "text-destructive")}>
                      {m.eh_entrada ? "+" : "−"}{numero(m.quantidade)}
                    </TableCell>
                    <TableCell className="tabular text-right">{m.saldo_apos === null ? "—" : numero(m.saldo_apos)}</TableCell>
                    <TableCell className="hidden text-muted-foreground md:table-cell">{m.motivo || m.observacao || "—"}</TableCell>
                    <TableCell className="hidden text-muted-foreground lg:table-cell">{m.usuario?.nome ?? "sistema"}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
          <Paginacao pagina={d.pagina} paginas={d.paginas} total={d.total} rotulo="movimentações" aoMudar={(p) => definir({ pagina: p === 1 ? undefined : p })} />
        </div>
      )}
    </div>
  );
}
