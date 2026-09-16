import { useQuery } from "@tanstack/react-query";
import { createFileRoute } from "@tanstack/react-router";

import { BotaoCsv, CabecalhoPagina } from "@/app/CabecalhoPagina";
import { GraficoSerie } from "@/components/charts/GraficoSerie";
import { ErroCarregamento, PaginaCarregando, Vazio } from "@/components/estado";
import { PeriodoControle } from "@/components/periodo/PeriodoControle";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Distribuicoes } from "@/features/dashboard/components/Distribuicoes";
import { urlCsv, vendasQuery } from "@/features/relatorios/api";
import { data as fmtData, mesAno, moeda, numero, percentual } from "@/lib/formatos";
import { paraApi, usePeriodo } from "@/lib/periodo";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/_auth/relatorios/vendas")({
  component: PaginaVendas,
});

function variacao(atual: number, anterior: number | null) {
  if (anterior === null || anterior === 0) return null;
  return (atual - anterior) / anterior;
}

function Tile({
  rotulo,
  valor,
  anterior,
  formato,
  comparar,
}: {
  rotulo: string;
  valor: number;
  anterior: number | null;
  formato: "moeda" | "numero";
  comparar: boolean;
}) {
  const f = formato === "moeda" ? moeda : numero;
  const v = variacao(valor, anterior);
  return (
    <Card className="gap-1 py-4">
      <CardHeader className="px-4 pb-0">
        <CardDescription>{rotulo}</CardDescription>
        <CardTitle className="tabular font-display text-2xl">{f(valor)}</CardTitle>
      </CardHeader>
      {comparar && (
        <CardContent className="px-4 text-xs text-muted-foreground">
          anterior: <span className="tabular">{anterior === null ? "—" : f(anterior)}</span>
          {v !== null && (
            <span className={cn("ml-2 font-medium", v > 0 ? "text-success" : v < 0 ? "text-destructive" : "")}>
              {percentual(v)}
            </span>
          )}
        </CardContent>
      )}
    </Card>
  );
}

function PaginaVendas() {
  const { valores } = usePeriodo();
  const consulta = useQuery(vendasQuery(valores));
  const d = consulta.data;
  const comparar = valores.comparar;

  return (
    <div className="space-y-6">
      <CabecalhoPagina
        titulo="Vendas por período"
        descricao="Pedidos válidos (sem rascunhos e cancelados), inclusive os que ainda aguardam pagamento."
        voltar={{ para: "/relatorios", rotulo: "Relatórios" }}
        acoes={<BotaoCsv href={urlCsv("vendas", paraApi(valores))} />}
      >
        <PeriodoControle />
      </CabecalhoPagina>

      {consulta.isError && !d ? (
        <ErroCarregamento erro={consulta.error} tentarDeNovo={() => consulta.refetch()} />
      ) : !d ? (
        <PaginaCarregando />
      ) : (
        <div className={cn("space-y-6 transition-opacity", consulta.isFetching && "opacity-70")}>
          <section className="grid gap-4 sm:grid-cols-3">
            <Tile rotulo="Total vendido" valor={d.total} anterior={d.total_anterior} formato="moeda" comparar={comparar} />
            <Tile rotulo="Pedidos" valor={d.qtd} anterior={d.qtd_anterior} formato="numero" comparar={comparar} />
            <Tile
              rotulo="Ticket médio"
              valor={d.ticket_medio}
              anterior={d.qtd_anterior && d.total_anterior !== null ? d.total_anterior / d.qtd_anterior : null}
              formato="moeda"
              comparar={comparar}
            />
          </section>

          <section className="grid gap-4 lg:grid-cols-3">
            <Card className="lg:col-span-2">
              <CardHeader>
                <CardTitle>Valor vendido</CardTitle>
                <CardDescription>
                  {d.periodo.rotulo} · por {d.periodo.granularidade === "mes" ? "mês" : "dia"}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <GraficoSerie
                  dados={d.por_periodo.map((l) => ({ data: l.data, valor: l.total, anterior: l.anterior }))}
                  granularidade={d.periodo.granularidade}
                  rotulo="Vendido"
                  formato="moeda"
                  comparar={comparar}
                />
              </CardContent>
            </Card>
            <Distribuicoes status={d.por_status} formas={d.por_forma} />
          </section>

          <Card>
            <CardHeader>
              <CardTitle>Detalhe por {d.periodo.granularidade === "mes" ? "mês" : "dia"}</CardTitle>
              <CardDescription>Só os {d.periodo.granularidade === "mes" ? "meses" : "dias"} com movimento</CardDescription>
            </CardHeader>
            <CardContent>
              {d.qtd === 0 ? (
                <Vazio titulo="Nenhuma venda no período" className="py-8" />
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>{d.periodo.granularidade === "mes" ? "Mês" : "Dia"}</TableHead>
                      <TableHead className="text-right">Pedidos</TableHead>
                      <TableHead className="text-right">Vendido</TableHead>
                      {comparar && <TableHead className="text-right">Anterior</TableHead>}
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {d.por_periodo
                      .filter((l) => l.qtd > 0 || (l.anterior ?? 0) > 0)
                      .map((l) => (
                        <TableRow key={l.data}>
                          <TableCell className="capitalize">
                            {d.periodo.granularidade === "mes" ? mesAno(l.data) : fmtData(l.data, "EEE, dd/MM")}
                          </TableCell>
                          <TableCell className="tabular text-right">{numero(l.qtd)}</TableCell>
                          <TableCell className="tabular text-right font-medium">{moeda(l.total)}</TableCell>
                          {comparar && (
                            <TableCell className="tabular text-right text-muted-foreground">
                              {l.anterior === null || l.anterior === undefined ? "—" : moeda(l.anterior)}
                            </TableCell>
                          )}
                        </TableRow>
                      ))}
                    <TableRow className="font-medium">
                      <TableCell>Total</TableCell>
                      <TableCell className="tabular text-right">{numero(d.qtd)}</TableCell>
                      <TableCell className="tabular text-right">{moeda(d.total)}</TableCell>
                      {comparar && (
                        <TableCell className="tabular text-right text-muted-foreground">
                          {d.total_anterior === null ? "—" : moeda(d.total_anterior)}
                        </TableCell>
                      )}
                    </TableRow>
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
