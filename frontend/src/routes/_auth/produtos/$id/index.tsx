import { useMutation, useQueryClient, useSuspenseQuery } from "@tanstack/react-query";
import { createFileRoute, Link, useRouter } from "@tanstack/react-router";
import { ArrowDownRight, ArrowUpRight, ImageIcon, Pencil } from "lucide-react";
import { toast } from "sonner";

import { CabecalhoPagina } from "@/app/CabecalhoPagina";
import { ConfirmarExclusao } from "@/components/ConfirmarExclusao";
import { PaginaCarregando, Vazio } from "@/components/estado";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { usePermissao } from "@/features/auth/queries";
import { chaves, excluirProduto, produtoQuery } from "@/features/produtos/api";
import { MovimentarEstoque } from "@/features/produtos/components/MovimentarEstoque";
import { COR_SITUACAO, ROTULO_SITUACAO } from "@/features/produtos/situacao";
import { dataHora, moeda, numero, percentual } from "@/lib/formatos";
import { cn } from "@/lib/utils";


export const Route = createFileRoute("/_auth/produtos/$id/")({
  loader: ({ context, params }) => context.queryClient.ensureQueryData(produtoQuery(Number(params.id))),
  pendingComponent: PaginaCarregando,
  component: PaginaProduto,
});

function Dado({ rotulo, valor }: { rotulo: string; valor?: React.ReactNode }) {
  return (
    <div>
      <div className="text-[11px] uppercase tracking-wide text-muted-foreground">{rotulo}</div>
      <div className="text-sm">{valor || "—"}</div>
    </div>
  );
}

function PaginaProduto() {
  const { id } = Route.useParams();
  const router = useRouter();
  const queryClient = useQueryClient();
  const permissao = usePermissao("catalogo");
  const { data: p } = useSuspenseQuery(produtoQuery(Number(id)));

  const excluir = useMutation({
    mutationFn: () => excluirProduto(p.id),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: chaves.todos });
      toast.success("Produto excluído.");
      void router.navigate({ to: "/produtos" });
    },
    onError: (erro: Error) => toast.error(erro.message),
  });

  return (
    <div className="space-y-6">
      <CabecalhoPagina
        titulo={p.nome_completo}
        voltar={{ para: "/produtos", rotulo: "Produtos" }}
        descricao={
          <span className="flex flex-wrap items-center gap-1.5">
            <Badge variant="secondary" className={cn("font-normal", COR_SITUACAO[p.situacao])}>{ROTULO_SITUACAO[p.situacao]}</Badge>
            {p.categoria && <Badge variant="outline" className="font-normal">{p.categoria.nome}</Badge>}
            {p.status === "inativo" && <Badge variant="outline" className="font-normal">Inativo</Badge>}
            {p.sku && <span className="text-xs text-muted-foreground">SKU {p.sku}</span>}
          </span>
        }
        acoes={
          permissao.escrever ? (
            <>
              <MovimentarEstoque produto={p} />
              <Button asChild size="sm" variant="outline">
                <Link to="/produtos/$id/editar" params={{ id }}><Pencil /> Editar</Link>
              </Button>
              {permissao.excluir && (
                <ConfirmarExclusao
                  titulo={`Excluir ${p.nome_completo}?`}
                  descricao="O histórico de movimentações e os itens de pedido que apontam para este produto serão afetados. Prefira marcar como inativo."
                  aoConfirmar={() => excluir.mutateAsync()}
                  pendente={excluir.isPending}
                />
              )}
            </>
          ) : undefined
        }
      />

      <div className="grid gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader><CardTitle>Ficha</CardTitle></CardHeader>
          <CardContent className="flex gap-5">
            <div className="flex size-28 shrink-0 items-center justify-center overflow-hidden rounded-lg border bg-muted">
              {p.foto ? <img src={p.foto} alt={p.nome} className="size-full object-cover" /> : <ImageIcon className="size-8 text-muted-foreground" />}
            </div>
            <div className="grid flex-1 grid-cols-2 gap-3 sm:grid-cols-3">
              <Dado rotulo="Tamanho" valor={p.tamanho} />
              <Dado rotulo="Cor" valor={p.cor} />
              <Dado rotulo="Marca" valor={p.marca} />
              <Dado rotulo="Fornecedor" valor={p.fornecedor ? (p.fornecedor.nome_fantasia || p.fornecedor.nome) : ""} />
              <Dado rotulo="Código interno" valor={p.codigo_interno} />
              <Dado rotulo="Localização" valor={p.localizacao} />
              {p.descricao && <div className="col-span-full"><Dado rotulo="Descrição" valor={<span className="whitespace-pre-line">{p.descricao}</span>} /></div>}
              {p.observacoes && <div className="col-span-full"><Dado rotulo="Observações" valor={<span className="whitespace-pre-line">{p.observacoes}</span>} /></div>}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>Estoque e preço</CardTitle></CardHeader>
          <CardContent className="grid grid-cols-2 gap-3">
            <div>
              <div className="text-[11px] uppercase tracking-wide text-muted-foreground">Saldo</div>
              <div className={cn("tabular font-display text-3xl font-semibold", p.situacao === "esgotado" && "text-destructive", p.situacao === "baixo" && "text-warning")}>{numero(p.quantidade_atual)}</div>
              <div className="text-xs text-muted-foreground">mín. {numero(p.estoque_minimo)}{p.estoque_maximo !== null && ` · máx. ${numero(p.estoque_maximo)}`}</div>
            </div>
            <div>
              <div className="text-[11px] uppercase tracking-wide text-muted-foreground">Em estoque (custo)</div>
              <div className="tabular font-display text-2xl font-semibold">{moeda(p.valor_em_estoque)}</div>
            </div>
            <Dado rotulo="Custo unitário" valor={moeda(p.custo_unitario)} />
            <Dado rotulo="Preço de venda" valor={moeda(p.preco_venda)} />
            <Dado rotulo="Margem estimada" valor={p.margem_estimada === null ? "—" : percentual(p.margem_estimada).replace("+", "")} />
            <Dado rotulo="Lucro por unidade" valor={moeda(p.preco_venda - p.custo_unitario)} />
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader className="flex-row items-center justify-between">
          <div>
            <CardTitle>Movimentações</CardTitle>
            <CardDescription>Últimas 30 · o saldo só muda por aqui</CardDescription>
          </div>
          <Link to="/produtos/movimentacoes" search={{ produto: p.id }} className="text-xs text-muted-foreground hover:text-foreground">ver todas</Link>
        </CardHeader>
        <CardContent>
          {p.movimentacoes_recentes.length === 0 ? (
            <Vazio titulo="Nenhuma movimentação ainda" descricao="Registre a entrada inicial para o saldo ficar rastreável." className="py-8" />
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Quando</TableHead>
                  <TableHead>Tipo</TableHead>
                  <TableHead className="text-right">Qtd.</TableHead>
                  <TableHead className="text-right">Saldo após</TableHead>
                  <TableHead className="hidden md:table-cell">Motivo</TableHead>
                  <TableHead className="hidden lg:table-cell">Quem</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {p.movimentacoes_recentes.map((m) => (
                  <TableRow key={m.id}>
                    <TableCell className="text-muted-foreground">{dataHora(m.data)}</TableCell>
                    <TableCell>
                      <span className="flex items-center gap-1.5">
                        {m.eh_entrada ? <ArrowUpRight className="size-3.5 text-success" /> : <ArrowDownRight className="size-3.5 text-destructive" />}
                        {m.tipo_rotulo}
                        {m.pedido_numero && <span className="text-xs text-muted-foreground">· pedido {m.pedido_numero}</span>}
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
          )}
        </CardContent>
      </Card>
    </div>
  );
}
