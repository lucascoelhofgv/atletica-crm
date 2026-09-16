import { useQuery } from "@tanstack/react-query";
import { createFileRoute, Link } from "@tanstack/react-router";
import { Download, Plus, Search, X } from "lucide-react";
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
import { clientesQuery, opcoesClienteQuery, urlExportarClientes } from "@/features/clientes/api";
import { moeda, numero } from "@/lib/formatos";
import { cn } from "@/lib/utils";

const buscaSchema = z.object({
  q: z.string().optional().catch(undefined),
  categoria: z.number().optional().catch(undefined),
  relacionamento: z.string().optional().catch(undefined),
  fgv: z.boolean().optional().catch(undefined),
  tag: z.number().optional().catch(undefined),
  pagina: z.number().optional().catch(undefined),
  ordenar: z.string().optional().catch(undefined),
});

export const Route = createFileRoute("/_auth/clientes/")({
  validateSearch: buscaSchema,
  component: PaginaClientes,
});

const TODOS = "__todos__";

const COR_RELACIONAMENTO: Record<string, string> = {
  novo: "bg-muted text-muted-foreground",
  ativo: "bg-success/15 text-success",
  recorrente: "bg-primary/15 text-primary",
  inativo: "bg-destructive/10 text-destructive",
};

function PaginaClientes() {
  const filtros = Route.useSearch();
  const navigate = Route.useNavigate();
  const permissao = usePermissao("crm");
  const consulta = useQuery(clientesQuery(filtros));
  const { data: opcoes } = useQuery(opcoesClienteQuery);
  const d = consulta.data;

  // Busca com debounce: digita local, URL atualiza depois de 300 ms.
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

  const temFiltro = !!(filtros.q || filtros.categoria || filtros.relacionamento || filtros.fgv || filtros.tag);

  return (
    <div className="space-y-4">
      <CabecalhoPagina
        titulo="Clientes"
        descricao="Contatos, alunos, torcedores e quem mais compra da Atlética."
        acoes={
          <>
            <Button asChild variant="outline" size="sm">
              <a href={urlExportarClientes(filtros)} download><Download /> CSV</a>
            </Button>
            {permissao.escrever && (
              <Button asChild size="sm">
                <Link to="/clientes/novo"><Plus /> Novo cliente</Link>
              </Button>
            )}
          </>
        }
      >
        <div className="flex flex-wrap items-center gap-3">
          <div className="relative w-full max-w-xs">
            <Search className="pointer-events-none absolute left-2.5 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder="Nome, e-mail, telefone, curso…"
              className="h-8 pl-8 pr-8"
              value={termo}
              onChange={(e) => setTermo(e.target.value)}
            />
            {termo && (
              <button type="button" onClick={() => setTermo("")} className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground" aria-label="Limpar busca">
                <X className="size-4" />
              </button>
            )}
          </div>
          <Select value={filtros.categoria ? String(filtros.categoria) : TODOS} onValueChange={(v) => definir({ categoria: v === TODOS ? undefined : Number(v), pagina: undefined })}>
            <SelectTrigger size="sm" className="w-52"><SelectValue placeholder="Categoria" /></SelectTrigger>
            <SelectContent>
              <SelectItem value={TODOS}>Todas as categorias</SelectItem>
              {opcoes?.categorias.map((c) => <SelectItem key={c.id} value={String(c.id)}>{c.nome}</SelectItem>)}
            </SelectContent>
          </Select>
          <Select value={filtros.relacionamento ?? TODOS} onValueChange={(v) => definir({ relacionamento: v === TODOS ? undefined : v, pagina: undefined })}>
            <SelectTrigger size="sm" className="w-40"><SelectValue placeholder="Status" /></SelectTrigger>
            <SelectContent>
              <SelectItem value={TODOS}>Todos os status</SelectItem>
              {opcoes?.relacionamentos.map((o) => <SelectItem key={o.valor} value={o.valor}>{o.rotulo}</SelectItem>)}
            </SelectContent>
          </Select>
          <div className="flex items-center gap-2">
            <Switch id="fgv" checked={!!filtros.fgv} onCheckedChange={(v) => definir({ fgv: v || undefined, pagina: undefined })} />
            <Label htmlFor="fgv" className="cursor-pointer text-xs font-normal text-muted-foreground">Só comunidade FGV</Label>
          </div>
          {temFiltro && (
            <Button variant="ghost" size="sm" onClick={() => { setTermo(""); void navigate({ search: {}, replace: true }); }}>
              Limpar filtros
            </Button>
          )}
        </div>
      </CabecalhoPagina>

      {consulta.isError && !d ? (
        <ErroCarregamento erro={consulta.error} tentarDeNovo={() => consulta.refetch()} />
      ) : !d ? (
        <SkeletonLinhas n={8} />
      ) : d.total === 0 ? (
        <Vazio
          titulo={temFiltro ? "Nenhum cliente com esses filtros" : "Nenhum cliente cadastrado"}
          descricao={temFiltro ? "Tente outra busca ou limpe os filtros." : "Cadastre o primeiro cliente para começar."}
          acao={permissao.escrever && !temFiltro ? <Button asChild size="sm"><Link to="/clientes/novo"><Plus /> Novo cliente</Link></Button> : undefined}
        />
      ) : (
        <div className={cn("space-y-3 transition-opacity", consulta.isFetching && "opacity-70")}>
          <div className="overflow-hidden rounded-xl border bg-card">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Cliente</TableHead>
                  <TableHead className="hidden md:table-cell">Curso</TableHead>
                  <TableHead className="hidden lg:table-cell">Categoria</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="hidden text-right sm:table-cell">Pedidos</TableHead>
                  <TableHead className="text-right">Gasto</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {d.resultados.map((c) => (
                  <TableRow key={c.id} className="cursor-pointer" onClick={() => void navigate({ to: "/clientes/$id", params: { id: String(c.id) } })}>
                    <TableCell>
                      <Link to="/clientes/$id" params={{ id: String(c.id) }} className="font-medium hover:underline" onClick={(e) => e.stopPropagation()}>
                        {c.nome_social || c.nome}
                      </Link>
                      <div className="flex flex-wrap items-center gap-1 text-xs text-muted-foreground">
                        {c.email || c.whatsapp || c.telefone || "sem contato"}
                        {c.tags.map((t) => (
                          <span key={t.id} className="rounded-full px-1.5 text-[10px] text-white" style={{ background: t.cor }}>{t.nome}</span>
                        ))}
                      </div>
                    </TableCell>
                    <TableCell className="hidden text-muted-foreground md:table-cell">
                      {c.curso || "—"}{c.periodo && <span className="text-xs"> · {c.periodo}</span>}
                    </TableCell>
                    <TableCell className="hidden text-muted-foreground lg:table-cell">{c.categoria?.nome ?? "—"}</TableCell>
                    <TableCell>
                      <Badge variant="secondary" className={cn("font-normal", COR_RELACIONAMENTO[c.relacionamento])}>{c.relacionamento_rotulo}</Badge>
                    </TableCell>
                    <TableCell className="tabular hidden text-right sm:table-cell">{numero(c.qtd_pedidos)}</TableCell>
                    <TableCell className="tabular text-right">{moeda(c.total_gasto)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
          <Paginacao pagina={d.pagina} paginas={d.paginas} total={d.total} rotulo="clientes" aoMudar={(p) => definir({ pagina: p === 1 ? undefined : p })} />
        </div>
      )}
    </div>
  );
}
