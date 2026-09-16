import { useQuery } from "@tanstack/react-query";
import { createFileRoute } from "@tanstack/react-router";
import { Search } from "lucide-react";
import { useMemo } from "react";
import { z } from "zod";

import { BotaoCsv, CabecalhoPagina } from "@/app/CabecalhoPagina";
import { ErroCarregamento, PaginaCarregando, Vazio } from "@/components/estado";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { clientesQuery, urlCsv } from "@/features/relatorios/api";
import { moeda, numero } from "@/lib/formatos";
import { cn } from "@/lib/utils";

const buscaSchema = z.object({
  recorrentes: z.boolean().optional().catch(undefined),
  q: z.string().optional().catch(undefined),
});

export const Route = createFileRoute("/_auth/relatorios/clientes")({
  validateSearch: buscaSchema,
  component: PaginaClientes,
});

function normalizar(s: string) {
  return s.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
}

function PaginaClientes() {
  const { recorrentes = false, q = "" } = Route.useSearch();
  const navigate = Route.useNavigate();
  const consulta = useQuery(clientesQuery(recorrentes));
  const d = consulta.data;

  const itens = useMemo(() => {
    if (!d) return [];
    const termo = normalizar(q.trim());
    if (!termo) return d.itens;
    return d.itens.filter((c) =>
      normalizar(`${c.nome} ${c.email} ${c.curso} ${c.categoria}`).includes(termo),
    );
  }, [d, q]);

  function definir(patch: { recorrentes?: boolean; q?: string }) {
    void navigate({
      search: (ant) => ({
        recorrentes: (patch.recorrentes ?? ant.recorrentes) || undefined,
        q: (patch.q ?? ant.q) || undefined,
      }),
      replace: true,
    });
  }

  return (
    <div className="space-y-6">
      <CabecalhoPagina
        titulo="Clientes"
        descricao="Ranking por pedidos válidos; o valor gasto considera só pedidos pagos, em separação, prontos ou entregues."
        voltar={{ para: "/relatorios", rotulo: "Relatórios" }}
        acoes={<BotaoCsv href={urlCsv("clientes", { recorrentes: recorrentes ? 1 : undefined })} />}
      >
        <div className="flex flex-wrap items-center gap-4">
          <div className="relative w-full max-w-xs">
            <Search className="pointer-events-none absolute left-2.5 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder="Buscar por nome, e-mail, curso…"
              className="h-8 pl-8"
              value={q}
              onChange={(e) => definir({ q: e.target.value })}
            />
          </div>
          <div className="flex items-center gap-2">
            <Switch id="recorrentes" checked={recorrentes} onCheckedChange={(v) => definir({ recorrentes: v })} />
            <Label htmlFor="recorrentes" className="cursor-pointer text-xs font-normal text-muted-foreground">
              Só recorrentes (2+ pedidos)
            </Label>
          </div>
        </div>
      </CabecalhoPagina>

      {consulta.isError && !d ? (
        <ErroCarregamento erro={consulta.error} tentarDeNovo={() => consulta.refetch()} />
      ) : !d ? (
        <PaginaCarregando />
      ) : (
        <Card className={cn("transition-opacity", consulta.isFetching && "opacity-70")}>
          <CardHeader>
            <CardTitle>{recorrentes ? "Clientes recorrentes" : "Todos os clientes"}</CardTitle>
            <CardDescription>
              {numero(itens.length)} de {numero(d.total)}
              {d.total >= 300 && " (limitado aos 300 primeiros; use o CSV para a lista completa)"}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {itens.length === 0 ? (
              <Vazio titulo="Nenhum cliente encontrado" className="py-8" />
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-8 text-right">#</TableHead>
                    <TableHead>Cliente</TableHead>
                    <TableHead className="hidden md:table-cell">Curso</TableHead>
                    <TableHead className="hidden lg:table-cell">Categoria</TableHead>
                    <TableHead className="text-right">Pedidos</TableHead>
                    <TableHead className="text-right">Gasto</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {itens.map((c, i) => (
                    <TableRow key={c.id}>
                      <TableCell className="tabular text-right text-muted-foreground">{i + 1}</TableCell>
                      <TableCell>
                        <a href={c.url || "/clientes/"} className="font-medium hover:underline">{c.nome}</a>
                        {c.email && <div className="text-xs text-muted-foreground">{c.email}</div>}
                      </TableCell>
                      <TableCell className="hidden text-muted-foreground md:table-cell">{c.curso || "—"}</TableCell>
                      <TableCell className="hidden text-muted-foreground lg:table-cell">{c.categoria || "—"}</TableCell>
                      <TableCell className="tabular text-right">{numero(c.pedidos)}</TableCell>
                      <TableCell className="tabular text-right font-medium">{moeda(c.gasto)}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
