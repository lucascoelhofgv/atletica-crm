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
import { fornecedoresQuery, opcoesFornecedorQuery } from "@/features/fornecedores/api";
import { Estrelas } from "@/features/fornecedores/components/Estrelas";
import { numero } from "@/lib/formatos";
import { cn } from "@/lib/utils";

const buscaSchema = z.object({
  q: z.string().optional().catch(undefined),
  categoria: z.string().optional().catch(undefined),
  status: z.string().optional().catch(undefined),
  pagina: z.number().optional().catch(undefined),
});

export const Route = createFileRoute("/_auth/fornecedores/")({
  validateSearch: buscaSchema,
  component: PaginaFornecedores,
});

const TODOS = "__todos__";

function PaginaFornecedores() {
  const filtros = Route.useSearch();
  const navigate = Route.useNavigate();
  const permissao = usePermissao("fornecedores");
  const consulta = useQuery(fornecedoresQuery(filtros));
  const { data: opcoes } = useQuery(opcoesFornecedorQuery);
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
  const temFiltro = !!(filtros.q || filtros.categoria || filtros.status);

  return (
    <div className="space-y-4">
      <CabecalhoPagina
        titulo="Fornecedores"
        descricao="Quem fornece produtos e serviços para a Atlética, com avaliações da equipe."
        acoes={permissao.escrever ? <Button asChild size="sm"><Link to="/fornecedores/novo"><Plus /> Novo fornecedor</Link></Button> : undefined}
      >
        <div className="flex flex-wrap items-center gap-3">
          <div className="relative w-full max-w-xs">
            <Search className="pointer-events-none absolute left-2.5 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
            <Input placeholder="Nome, contato, o que fornece…" className="h-8 pl-8 pr-8" value={termo} onChange={(e) => setTermo(e.target.value)} />
            {termo && <button type="button" onClick={() => setTermo("")} className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground" aria-label="Limpar busca"><X className="size-4" /></button>}
          </div>
          <Select value={filtros.categoria ?? TODOS} onValueChange={(v) => definir({ categoria: v === TODOS ? undefined : v, pagina: undefined })}>
            <SelectTrigger size="sm" className="w-48"><SelectValue placeholder="Categoria" /></SelectTrigger>
            <SelectContent>
              <SelectItem value={TODOS}>Todas as categorias</SelectItem>
              {opcoes?.categorias.map((o) => <SelectItem key={o.valor} value={o.valor}>{o.rotulo}</SelectItem>)}
            </SelectContent>
          </Select>
          <Select value={filtros.status ?? TODOS} onValueChange={(v) => definir({ status: v === TODOS ? undefined : v, pagina: undefined })}>
            <SelectTrigger size="sm" className="w-44"><SelectValue placeholder="Status" /></SelectTrigger>
            <SelectContent>
              <SelectItem value={TODOS}>Ativos e inativos</SelectItem>
              {opcoes?.status.map((o) => <SelectItem key={o.valor} value={o.valor}>{o.rotulo}</SelectItem>)}
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
        <Vazio titulo={temFiltro ? "Nenhum fornecedor com esses filtros" : "Nenhum fornecedor cadastrado"}
          acao={permissao.escrever && !temFiltro ? <Button asChild size="sm"><Link to="/fornecedores/novo"><Plus /> Novo fornecedor</Link></Button> : undefined} />
      ) : (
        <div className={cn("space-y-3 transition-opacity", consulta.isFetching && "opacity-70")}>
          <div className="overflow-hidden rounded-xl border bg-card">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Fornecedor</TableHead>
                  <TableHead className="hidden md:table-cell">Categoria</TableHead>
                  <TableHead className="hidden lg:table-cell">Contato</TableHead>
                  <TableHead>Avaliação</TableHead>
                  <TableHead className="hidden text-right sm:table-cell">Produtos</TableHead>
                  <TableHead>Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {d.resultados.map((f) => (
                  <TableRow key={f.id} className="cursor-pointer" onClick={() => void navigate({ to: "/fornecedores/$id", params: { id: String(f.id) } })}>
                    <TableCell>
                      <Link to="/fornecedores/$id" params={{ id: String(f.id) }} className="font-medium hover:underline" onClick={(e) => e.stopPropagation()}>{f.nome_exibicao}</Link>
                      {f.nome_fantasia && <div className="text-xs text-muted-foreground">{f.nome}</div>}
                    </TableCell>
                    <TableCell className="hidden text-muted-foreground md:table-cell">{f.categoria_rotulo}</TableCell>
                    <TableCell className="hidden text-muted-foreground lg:table-cell">{[f.contato_nome, f.whatsapp || f.telefone || f.email].filter(Boolean).join(" · ") || "—"}</TableCell>
                    <TableCell>
                      {f.nota_media === null ? (
                        <span className="text-xs text-muted-foreground">sem avaliação</span>
                      ) : (
                        <span className="flex items-center gap-1.5"><Estrelas valor={f.nota_media} tamanho="size-3.5" /><span className="tabular text-xs text-muted-foreground">{f.nota_media.toFixed(1)} ({f.qtd_avaliacoes})</span></span>
                      )}
                    </TableCell>
                    <TableCell className="tabular hidden text-right sm:table-cell">{numero(f.qtd_produtos)}</TableCell>
                    <TableCell><Badge variant={f.status === "ativo" ? "secondary" : "outline"} className="font-normal">{f.status_rotulo}</Badge></TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
          <Paginacao pagina={d.pagina} paginas={d.paginas} total={d.total} rotulo="fornecedores" aoMudar={(p) => definir({ pagina: p === 1 ? undefined : p })} />
        </div>
      )}
    </div>
  );
}
