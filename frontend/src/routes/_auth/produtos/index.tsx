import { useQuery } from "@tanstack/react-query";
import { createFileRoute, Link } from "@tanstack/react-router";
import { Download, History, ImageIcon, Plus, Search, X } from "lucide-react";
import { useEffect, useState } from "react";
import { z } from "zod";

import { CabecalhoPagina } from "@/app/CabecalhoPagina";
import { ErroCarregamento, SkeletonLinhas, Vazio } from "@/components/estado";
import { Paginacao } from "@/components/Paginacao";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { usePermissao } from "@/features/auth/queries";
import { opcoesProdutoQuery, produtosQuery, urlExportarProdutos } from "@/features/produtos/api";
import { COR_SITUACAO, ROTULO_SITUACAO } from "@/features/produtos/situacao";
import type { Situacao } from "@/features/produtos/types";
import { moeda, numero } from "@/lib/formatos";
import { cn } from "@/lib/utils";

const buscaSchema = z.object({
  q: z.string().optional().catch(undefined),
  categoria: z.number().optional().catch(undefined),
  fornecedor: z.number().optional().catch(undefined),
  status: z.string().optional().catch(undefined),
  situacao: z.enum(["ok", "baixo", "esgotado"]).optional().catch(undefined),
  pagina: z.number().optional().catch(undefined),
  ordenar: z.string().optional().catch(undefined),
});

export const Route = createFileRoute("/_auth/produtos/")({
  validateSearch: buscaSchema,
  component: PaginaProdutos,
});

const TODOS = "__todos__";

function PaginaProdutos() {
  const filtros = Route.useSearch();
  const navigate = Route.useNavigate();
  const permissao = usePermissao("catalogo");
  const consulta = useQuery(produtosQuery(filtros));
  const { data: opcoes } = useQuery(opcoesProdutoQuery);
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
  const temFiltro = !!(filtros.q || filtros.categoria || filtros.fornecedor || filtros.status || filtros.situacao);

  return (
    <div className="space-y-4">
      <CabecalhoPagina
        titulo="Produtos e estoque"
        descricao="Catálogo, saldo por produto e histórico de movimentações."
        acoes={
          <>
            <Button asChild variant="outline" size="sm">
              <Link to="/produtos/movimentacoes"><History /> Movimentações</Link>
            </Button>
            <Button asChild variant="outline" size="sm">
              <a href={urlExportarProdutos(filtros)} download><Download /> CSV</a>
            </Button>
            {permissao.escrever && (
              <Button asChild size="sm">
                <Link to="/produtos/novo"><Plus /> Novo produto</Link>
              </Button>
            )}
          </>
        }
      >
        <div className="flex flex-wrap items-center gap-3">
          <div className="relative w-full max-w-xs">
            <Search className="pointer-events-none absolute left-2.5 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
            <Input placeholder="Nome, SKU, código, marca…" className="h-8 pl-8 pr-8" value={termo} onChange={(e) => setTermo(e.target.value)} />
            {termo && (
              <button type="button" onClick={() => setTermo("")} className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground" aria-label="Limpar busca">
                <X className="size-4" />
              </button>
            )}
          </div>
          <ToggleGroup type="single" variant="outline" size="sm" value={filtros.situacao ?? "todos"}
            onValueChange={(v) => v && definir({ situacao: v === "todos" ? undefined : (v as Situacao), pagina: undefined })}>
            <ToggleGroupItem value="todos" className="px-3">Todos</ToggleGroupItem>
            <ToggleGroupItem value="baixo" className="px-3">Baixo</ToggleGroupItem>
            <ToggleGroupItem value="esgotado" className="px-3">Esgotados</ToggleGroupItem>
          </ToggleGroup>
          <Select value={filtros.categoria ? String(filtros.categoria) : TODOS} onValueChange={(v) => definir({ categoria: v === TODOS ? undefined : Number(v), pagina: undefined })}>
            <SelectTrigger size="sm" className="w-48"><SelectValue placeholder="Categoria" /></SelectTrigger>
            <SelectContent>
              <SelectItem value={TODOS}>Todas as categorias</SelectItem>
              {opcoes?.categorias.map((c) => <SelectItem key={c.id} value={String(c.id)}>{c.nome}</SelectItem>)}
            </SelectContent>
          </Select>
          <Select value={filtros.status ?? TODOS} onValueChange={(v) => definir({ status: v === TODOS ? undefined : v, pagina: undefined })}>
            <SelectTrigger size="sm" className="w-44"><SelectValue placeholder="Status" /></SelectTrigger>
            <SelectContent>
              <SelectItem value={TODOS}>Ativos e inativos</SelectItem>
              {opcoes?.status.map((o) => <SelectItem key={o.valor} value={o.valor}>{o.rotulo}</SelectItem>)}
            </SelectContent>
          </Select>
          {temFiltro && (
            <Button variant="ghost" size="sm" onClick={() => { setTermo(""); void navigate({ search: {}, replace: true }); }}>Limpar filtros</Button>
          )}
        </div>
      </CabecalhoPagina>

      {consulta.isError && !d ? (
        <ErroCarregamento erro={consulta.error} tentarDeNovo={() => consulta.refetch()} />
      ) : !d ? (
        <SkeletonLinhas n={8} />
      ) : d.total === 0 ? (
        <Vazio titulo={temFiltro ? "Nenhum produto com esses filtros" : "Nenhum produto cadastrado"}
          acao={permissao.escrever && !temFiltro ? <Button asChild size="sm"><Link to="/produtos/novo"><Plus /> Novo produto</Link></Button> : undefined} />
      ) : (
        <div className={cn("space-y-3 transition-opacity", consulta.isFetching && "opacity-70")}>
          <div className="overflow-hidden rounded-xl border bg-card">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Produto</TableHead>
                  <TableHead className="hidden md:table-cell">Categoria</TableHead>
                  <TableHead className="text-right">Saldo</TableHead>
                  <TableHead className="hidden text-right lg:table-cell">Custo</TableHead>
                  <TableHead className="text-right">Preço</TableHead>
                  <TableHead className="hidden text-right lg:table-cell">Em estoque</TableHead>
                  <TableHead>Situação</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {d.resultados.map((p) => (
                  <TableRow key={p.id} className="cursor-pointer" onClick={() => void navigate({ to: "/produtos/$id", params: { id: String(p.id) } })}>
                    <TableCell>
                      <div className="flex items-center gap-3">
                        <div className="flex size-9 shrink-0 items-center justify-center overflow-hidden rounded-md border bg-muted">
                          {p.foto ? <img src={p.foto} alt="" className="size-full object-cover" /> : <ImageIcon className="size-4 text-muted-foreground" />}
                        </div>
                        <div className="min-w-0">
                          <Link to="/produtos/$id" params={{ id: String(p.id) }} className="font-medium hover:underline" onClick={(e) => e.stopPropagation()}>
                            {p.nome_completo}
                          </Link>
                          <div className="text-xs text-muted-foreground">
                            {[p.sku, p.codigo_interno].filter(Boolean).join(" · ") || "sem código"}
                            {p.status === "inativo" && <Badge variant="outline" className="ml-2 font-normal">inativo</Badge>}
                          </div>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell className="hidden text-muted-foreground md:table-cell">{p.categoria?.nome ?? "—"}</TableCell>
                    <TableCell className="tabular text-right font-medium">{numero(p.quantidade_atual)}</TableCell>
                    <TableCell className="tabular hidden text-right text-muted-foreground lg:table-cell">{moeda(p.custo_unitario)}</TableCell>
                    <TableCell className="tabular text-right">{moeda(p.preco_venda)}</TableCell>
                    <TableCell className="tabular hidden text-right text-muted-foreground lg:table-cell">{moeda(p.valor_em_estoque)}</TableCell>
                    <TableCell><Badge variant="secondary" className={cn("font-normal", COR_SITUACAO[p.situacao])}>{ROTULO_SITUACAO[p.situacao]}</Badge></TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
          <Paginacao pagina={d.pagina} paginas={d.paginas} total={d.total} rotulo="produtos" aoMudar={(p) => definir({ pagina: p === 1 ? undefined : p })} />
        </div>
      )}
    </div>
  );
}
