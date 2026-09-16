import { useQuery } from "@tanstack/react-query";
import { createFileRoute } from "@tanstack/react-router";
import { z } from "zod";

import { CabecalhoPagina } from "@/app/CabecalhoPagina";
import { ErroCarregamento, SkeletonLinhas, Vazio } from "@/components/estado";
import { Paginacao } from "@/components/Paginacao";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { useUsuario } from "@/features/auth/queries";
import { acessosQuery } from "@/features/membros/api";
import { dataHora } from "@/lib/formatos";
import { cn } from "@/lib/utils";

const buscaSchema = z.object({ pagina: z.number().optional().catch(undefined) });

export const Route = createFileRoute("/_auth/administracao/acessos")({
  validateSearch: buscaSchema,
  component: PaginaAcessos,
});

function PaginaAcessos() {
  const filtros = Route.useSearch();
  const navigate = Route.useNavigate();
  const usuario = useUsuario();
  const consulta = useQuery(acessosQuery(filtros));
  const d = consulta.data;

  return (
    <div className="space-y-4">
      <CabecalhoPagina titulo="Acessos" descricao={usuario.eh_admin ? "Logins de toda a equipe, com sucesso ou falha." : "Seus logins recentes."} />
      {consulta.isError && !d ? (
        <ErroCarregamento erro={consulta.error} tentarDeNovo={() => consulta.refetch()} />
      ) : !d ? (
        <SkeletonLinhas n={10} />
      ) : d.total === 0 ? (
        <Vazio titulo="Nenhum acesso registrado" />
      ) : (
        <div className={cn("space-y-3 transition-opacity", consulta.isFetching && "opacity-70")}>
          <div className="overflow-hidden rounded-xl border bg-card">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Quando</TableHead>
                  <TableHead>Quem</TableHead>
                  <TableHead>Resultado</TableHead>
                  <TableHead className="hidden md:table-cell">IP</TableHead>
                  <TableHead className="hidden lg:table-cell">Navegador</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {d.resultados.map((a) => (
                  <TableRow key={a.id}>
                    <TableCell className="text-muted-foreground">{dataHora(a.momento)}</TableCell>
                    <TableCell className="font-medium">{a.usuario?.nome ?? "usuário desconhecido"}</TableCell>
                    <TableCell><Badge variant="secondary" className={cn("font-normal", a.sucesso ? "bg-success/15 text-success" : "bg-destructive/10 text-destructive")}>{a.sucesso ? "Entrou" : "Falhou"}</Badge></TableCell>
                    <TableCell className="tabular hidden text-muted-foreground md:table-cell">{a.ip ?? "—"}</TableCell>
                    <TableCell className="hidden max-w-xs truncate text-xs text-muted-foreground lg:table-cell" title={a.agente}>{a.agente || "—"}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
          <Paginacao pagina={d.pagina} paginas={d.paginas} total={d.total} rotulo="acessos" aoMudar={(p) => void navigate({ search: { pagina: p === 1 ? undefined : p }, replace: true })} />
        </div>
      )}
    </div>
  );
}
