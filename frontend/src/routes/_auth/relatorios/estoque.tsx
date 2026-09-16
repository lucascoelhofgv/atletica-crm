import { useQuery } from "@tanstack/react-query";
import { createFileRoute } from "@tanstack/react-router";
import { z } from "zod";

import { BotaoCsv, CabecalhoPagina } from "@/app/CabecalhoPagina";
import { ErroCarregamento, PaginaCarregando, Vazio } from "@/components/estado";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { estoqueQuery, urlCsv } from "@/features/relatorios/api";
import type { SituacaoEstoque } from "@/features/relatorios/types";
import { moeda, numero } from "@/lib/formatos";
import { cn } from "@/lib/utils";

const buscaSchema = z.object({
  situacao: z.enum(["ok", "baixo", "esgotado"]).optional().catch(undefined),
});

export const Route = createFileRoute("/_auth/relatorios/estoque")({
  validateSearch: buscaSchema,
  component: PaginaEstoque,
});

const ROTULO: Record<SituacaoEstoque, string> = { ok: "Normal", baixo: "Baixo", esgotado: "Esgotado" };
const COR: Record<SituacaoEstoque, string> = {
  ok: "bg-success/15 text-success",
  baixo: "bg-warning/20 text-warning",
  esgotado: "bg-destructive/15 text-destructive",
};

function PaginaEstoque() {
  const { situacao } = Route.useSearch();
  const navigate = Route.useNavigate();
  const consulta = useQuery(estoqueQuery(situacao));
  const d = consulta.data;
  const itens = d ? (situacao === "ok" ? d.itens.filter((i) => i.situacao === "ok") : d.itens) : [];

  return (
    <div className="space-y-6">
      <CabecalhoPagina
        titulo="Estoque atual"
        descricao="Foto de agora dos produtos ativos: saldo, mínimo e valor a custo."
        voltar={{ para: "/relatorios", rotulo: "Relatórios" }}
        acoes={<BotaoCsv href={urlCsv("estoque", { situacao: situacao === "ok" ? undefined : situacao })} />}
      >
        <ToggleGroup
          type="single"
          variant="outline"
          size="sm"
          value={situacao ?? "todos"}
          onValueChange={(v) =>
            v && navigate({ search: { situacao: v === "todos" ? undefined : (v as SituacaoEstoque) }, replace: true })
          }
        >
          <ToggleGroupItem value="todos" className="px-3">Todos</ToggleGroupItem>
          <ToggleGroupItem value="ok" className="px-3">Normal</ToggleGroupItem>
          <ToggleGroupItem value="baixo" className="px-3">Estoque baixo</ToggleGroupItem>
          <ToggleGroupItem value="esgotado" className="px-3">Esgotados</ToggleGroupItem>
        </ToggleGroup>
      </CabecalhoPagina>

      {consulta.isError && !d ? (
        <ErroCarregamento erro={consulta.error} tentarDeNovo={() => consulta.refetch()} />
      ) : !d ? (
        <PaginaCarregando />
      ) : (
        <div className={cn("space-y-6 transition-opacity", consulta.isFetching && "opacity-70")}>
          {!situacao && (
            <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
              <Card className="gap-1 py-4 lg:col-span-2">
                <CardHeader className="px-4 pb-0">
                  <CardDescription>Valor em estoque (a custo)</CardDescription>
                  <CardTitle className="tabular font-display text-2xl">{moeda(d.valor_total)}</CardTitle>
                </CardHeader>
                <CardContent className="px-4 text-xs text-muted-foreground">
                  {numero(d.unidades)} unidades em {numero(d.itens.length)} produtos
                </CardContent>
              </Card>
              {(["ok", "baixo", "esgotado"] as const).map((s) => (
                <Card key={s} className="gap-1 py-4">
                  <CardHeader className="px-4 pb-0">
                    <CardDescription>{ROTULO[s]}</CardDescription>
                    <CardTitle className="tabular font-display text-2xl">{numero(d.resumo[s])}</CardTitle>
                  </CardHeader>
                  <CardContent className="px-4 text-xs text-muted-foreground">produtos</CardContent>
                </Card>
              ))}
            </section>
          )}

          <Card>
            <CardHeader>
              <CardTitle>{situacao ? `Produtos com estoque ${ROTULO[situacao].toLowerCase()}` : "Todos os produtos ativos"}</CardTitle>
              <CardDescription>{numero(itens.length)} produtos</CardDescription>
            </CardHeader>
            <CardContent>
              {itens.length === 0 ? (
                <Vazio titulo="Nenhum produto nesta situação" className="py-8" />
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Produto</TableHead>
                      <TableHead className="hidden sm:table-cell">Categoria</TableHead>
                      <TableHead className="text-right">Saldo</TableHead>
                      <TableHead className="hidden text-right md:table-cell">Mínimo</TableHead>
                      <TableHead className="hidden text-right md:table-cell">Custo un.</TableHead>
                      <TableHead className="text-right">Valor</TableHead>
                      <TableHead>Situação</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {itens.map((i) => (
                      <TableRow key={i.id}>
                        <TableCell className="font-medium">
                          <a href={i.url || "/produtos/"} className="hover:underline">
                            {i.nome}
                            {i.tamanho && i.tamanho !== "único" && (
                              <span className="text-muted-foreground"> · {i.tamanho}</span>
                            )}
                          </a>
                          {i.sku && <span className="ml-1 text-xs text-muted-foreground">{i.sku}</span>}
                        </TableCell>
                        <TableCell className="hidden text-muted-foreground sm:table-cell">{i.categoria || "—"}</TableCell>
                        <TableCell className="tabular text-right">{numero(i.saldo)}</TableCell>
                        <TableCell className="tabular hidden text-right text-muted-foreground md:table-cell">{numero(i.minimo)}</TableCell>
                        <TableCell className="tabular hidden text-right text-muted-foreground md:table-cell">{moeda(i.custo_unitario)}</TableCell>
                        <TableCell className="tabular text-right">{moeda(i.valor_em_estoque)}</TableCell>
                        <TableCell>
                          <Badge variant="secondary" className={cn("font-normal", COR[i.situacao])}>{ROTULO[i.situacao]}</Badge>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
