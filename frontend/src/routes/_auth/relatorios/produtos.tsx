import { useQuery } from "@tanstack/react-query";
import { createFileRoute } from "@tanstack/react-router";

import { BotaoCsv, CabecalhoPagina } from "@/app/CabecalhoPagina";
import { GraficoBarras } from "@/components/charts/GraficoBarras";
import { ErroCarregamento, PaginaCarregando, Vazio } from "@/components/estado";
import { PeriodoControle } from "@/components/periodo/PeriodoControle";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { produtosQuery, urlCsv } from "@/features/relatorios/api";
import { moeda, numero, percentual } from "@/lib/formatos";
import { paraApi, usePeriodo } from "@/lib/periodo";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/_auth/relatorios/produtos")({
  component: PaginaProdutos,
});

function rotuloProduto(i: { produto: string; tamanho: string }) {
  return i.tamanho && i.tamanho !== "único" ? `${i.produto} · ${i.tamanho}` : i.produto;
}

function PaginaProdutos() {
  const { valores } = usePeriodo();
  const consulta = useQuery(produtosQuery(valores));
  const d = consulta.data;

  return (
    <div className="space-y-6">
      <CabecalhoPagina
        titulo="Produtos vendidos"
        descricao="Unidades e receita por produto nos pedidos válidos do período."
        voltar={{ para: "/relatorios", rotulo: "Relatórios" }}
        acoes={<BotaoCsv href={urlCsv("produtos", paraApi(valores))} />}
      >
        <PeriodoControle />
      </CabecalhoPagina>

      {consulta.isError && !d ? (
        <ErroCarregamento erro={consulta.error} tentarDeNovo={() => consulta.refetch()} />
      ) : !d ? (
        <PaginaCarregando />
      ) : d.itens.length === 0 ? (
        <Vazio titulo="Nenhum produto vendido no período" descricao="Ajuste o período ou registre pedidos." />
      ) : (
        <div className={cn("grid gap-4 lg:grid-cols-5 transition-opacity", consulta.isFetching && "opacity-70")}>
          <Card className="lg:col-span-2">
            <CardHeader>
              <CardTitle>Top 10 em unidades</CardTitle>
              <CardDescription>
                {numero(d.total_qtd)} unidades · {moeda(d.total_receita)} no período
              </CardDescription>
            </CardHeader>
            <CardContent>
              <GraficoBarras
                rotuloValor="Unidades"
                dados={d.itens.slice(0, 10).map((i) => ({
                  nome: rotuloProduto(i),
                  valor: i.qtd,
                  detalhe: `Receita: ${moeda(i.receita)} (${percentual(i.participacao).replace("+", "")})`,
                }))}
              />
            </CardContent>
          </Card>

          <Card className="lg:col-span-3">
            <CardHeader>
              <CardTitle>Todos os produtos</CardTitle>
              <CardDescription>Ordenado por unidades vendidas</CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Produto</TableHead>
                    <TableHead className="hidden sm:table-cell">Categoria</TableHead>
                    <TableHead className="text-right">Un.</TableHead>
                    <TableHead className="text-right">Pedidos</TableHead>
                    <TableHead className="text-right">Receita</TableHead>
                    <TableHead className="hidden w-32 md:table-cell">Participação</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {d.itens.map((i) => (
                    <TableRow key={i.produto_id}>
                      <TableCell className="font-medium">
                        {rotuloProduto(i)}
                        {i.sku && <span className="ml-1 text-xs text-muted-foreground">{i.sku}</span>}
                      </TableCell>
                      <TableCell className="hidden text-muted-foreground sm:table-cell">{i.categoria || "—"}</TableCell>
                      <TableCell className="tabular text-right">{numero(i.qtd)}</TableCell>
                      <TableCell className="tabular text-right text-muted-foreground">{numero(i.pedidos)}</TableCell>
                      <TableCell className="tabular text-right">{moeda(i.receita)}</TableCell>
                      <TableCell className="hidden md:table-cell">
                        <div className="flex items-center gap-2">
                          <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-muted">
                            <div className="h-full rounded-full bg-primary" style={{ width: `${Math.max(2, i.participacao * 100)}%` }} />
                          </div>
                          <span className="tabular w-11 text-right text-xs text-muted-foreground">
                            {percentual(i.participacao).replace("+", "")}
                          </span>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
