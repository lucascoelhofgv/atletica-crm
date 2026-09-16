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
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { usePermissao } from "@/features/auth/queries";
import { opcoesPedidoQuery, pedidosQuery } from "@/features/pedidos/api";
import { COR_PAGAMENTO, COR_STATUS } from "@/features/pedidos/status";
import { data as fmtData, moeda, numero } from "@/lib/formatos";
import { cn } from "@/lib/utils";

const buscaSchema = z.object({
  q: z.string().optional().catch(undefined),
  status: z.string().optional().catch(undefined),
  status_pagamento: z.string().optional().catch(undefined),
  forma_pagamento: z.string().optional().catch(undefined),
  cliente: z.number().optional().catch(undefined),
  pagina: z.number().optional().catch(undefined),
});

export const Route = createFileRoute("/_auth/pedidos/")({
  validateSearch: buscaSchema,
  component: PaginaPedidos,
});

const TODOS = "__todos__";

function PaginaPedidos() {
  const filtros = Route.useSearch();
  const navigate = Route.useNavigate();
  const permissao = usePermissao("vendas");
  const consulta = useQuery(pedidosQuery(filtros));
  const { data: opcoes } = useQuery(opcoesPedidoQuery);
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
  const temFiltro = !!(filtros.q || filtros.status || filtros.status_pagamento || filtros.forma_pagamento || filtros.cliente);

  return (
    <div className="space-y-4">
      <CabecalhoPagina
        titulo="Pedidos"
        descricao="Vendas, status de entrega e pagamento."
        acoes={permissao.escrever ? <Button asChild size="sm"><Link to="/pedidos/novo"><Plus /> Novo pedido</Link></Button> : undefined}
      >
        <div className="flex flex-wrap items-center gap-3">
          <div className="relative w-full max-w-xs">
            <Search className="pointer-events-none absolute left-2.5 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
            <Input placeholder="Número, cliente ou produto…" className="h-8 pl-8 pr-8" value={termo} onChange={(e) => setTermo(e.target.value)} />
            {termo && (
              <button type="button" onClick={() => setTermo("")} className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground" aria-label="Limpar busca"><X className="size-4" /></button>
            )}
          </div>
          <Select value={filtros.status ?? TODOS} onValueChange={(v) => definir({ status: v === TODOS ? undefined : v, pagina: undefined })}>
            <SelectTrigger size="sm" className="w-48"><SelectValue placeholder="Status" /></SelectTrigger>
            <SelectContent>
              <SelectItem value={TODOS}>Todos os status</SelectItem>
              {opcoes?.status.map((o) => <SelectItem key={o.valor} value={o.valor}>{o.rotulo}</SelectItem>)}
            </SelectContent>
          </Select>
          <Select value={filtros.status_pagamento ?? TODOS} onValueChange={(v) => definir({ status_pagamento: v === TODOS ? undefined : v, pagina: undefined })}>
            <SelectTrigger size="sm" className="w-52"><SelectValue placeholder="Pagamento" /></SelectTrigger>
            <SelectContent>
              <SelectItem value={TODOS}>Qualquer pagamento</SelectItem>
              {opcoes?.status_pagamento.map((o) => <SelectItem key={o.valor} value={o.valor}>{o.rotulo}</SelectItem>)}
            </SelectContent>
          </Select>
          {temFiltro && <Button variant="ghost" size="sm" onClick={() => { setTermo(""); void navigate({ search: {}, replace: true }); }}>Limpar filtros</Button>}
        </div>
      </CabecalhoPagina>

      {consulta.isError && !d ? (
        <ErroCarregamento erro={consulta.error} tentarDeNovo={() => consulta.refetch()} />
      ) : !d ? (
        <SkeletonLinhas n={8} />
      ) : d.total === 0 ? (
        <Vazio titulo={temFiltro ? "Nenhum pedido com esses filtros" : "Nenhum pedido ainda"}
          acao={permissao.escrever && !temFiltro ? <Button asChild size="sm"><Link to="/pedidos/novo"><Plus /> Novo pedido</Link></Button> : undefined} />
      ) : (
        <div className={cn("space-y-3 transition-opacity", consulta.isFetching && "opacity-70")}>
          <div className="overflow-hidden rounded-xl border bg-card">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Pedido</TableHead>
                  <TableHead>Cliente</TableHead>
                  <TableHead className="hidden md:table-cell">Data</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="hidden lg:table-cell">Pagamento</TableHead>
                  <TableHead className="hidden text-right sm:table-cell">Itens</TableHead>
                  <TableHead className="text-right">Total</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {d.resultados.map((p) => (
                  <TableRow key={p.id} className="cursor-pointer" onClick={() => void navigate({ to: "/pedidos/$id", params: { id: String(p.id) } })}>
                    <TableCell>
                      <Link to="/pedidos/$id" params={{ id: String(p.id) }} className="tabular font-medium hover:underline" onClick={(e) => e.stopPropagation()}>
                        {p.numero || `rascunho #${p.id}`}
                      </Link>
                    </TableCell>
                    <TableCell>{p.cliente.nome_social || p.cliente.nome}</TableCell>
                    <TableCell className="hidden text-muted-foreground md:table-cell">{fmtData(p.data_compra)}</TableCell>
                    <TableCell><Badge variant="secondary" className={cn("font-normal", COR_STATUS[p.status])}>{p.status_rotulo}</Badge></TableCell>
                    <TableCell className="hidden lg:table-cell">
                      <Badge variant="secondary" className={cn("font-normal", COR_PAGAMENTO[p.status_pagamento])}>{p.status_pagamento_rotulo}</Badge>
                      <span className="ml-2 text-xs text-muted-foreground">{p.forma_pagamento_rotulo}</span>
                    </TableCell>
                    <TableCell className="tabular hidden text-right sm:table-cell">{numero(p.qtd_itens)}</TableCell>
                    <TableCell className="tabular text-right font-medium">{moeda(p.valor_total)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
          <Paginacao pagina={d.pagina} paginas={d.paginas} total={d.total} rotulo="pedidos" aoMudar={(p) => definir({ pagina: p === 1 ? undefined : p })} />
        </div>
      )}
    </div>
  );
}
