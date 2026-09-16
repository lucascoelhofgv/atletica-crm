import { useQuery } from "@tanstack/react-query";
import { createFileRoute } from "@tanstack/react-router";
import { Search, X } from "lucide-react";
import { useEffect, useState } from "react";
import { z } from "zod";

import { CabecalhoPagina } from "@/app/CabecalhoPagina";
import { ErroCarregamento, SkeletonLinhas, Vazio } from "@/components/estado";
import { Paginacao } from "@/components/Paginacao";
import { Input } from "@/components/ui/input";
import { atividadesQuery } from "@/features/membros/api";
import { dataHora, relativo } from "@/lib/formatos";
import { cn } from "@/lib/utils";

const buscaSchema = z.object({
  q: z.string().optional().catch(undefined),
  pagina: z.number().optional().catch(undefined),
});

export const Route = createFileRoute("/_auth/administracao/historico")({
  validateSearch: buscaSchema,
  component: PaginaHistorico,
});

function PaginaHistorico() {
  const filtros = Route.useSearch();
  const navigate = Route.useNavigate();
  const consulta = useQuery(atividadesQuery(filtros));
  const d = consulta.data;
  const [termo, setTermo] = useState(filtros.q ?? "");
  useEffect(() => {
    const t = window.setTimeout(() => {
      if ((filtros.q ?? "") !== termo) void navigate({ search: { q: termo || undefined }, replace: true });
    }, 300);
    return () => window.clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [termo]);

  return (
    <div className="space-y-4">
      <CabecalhoPagina titulo="Histórico de atividades" descricao="Tudo que a equipe fez no CRM, do mais recente ao mais antigo.">
        <div className="relative w-full max-w-xs">
          <Search className="pointer-events-none absolute left-2.5 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input placeholder="Ação, registro ou pessoa…" className="h-8 pl-8 pr-8" value={termo} onChange={(e) => setTermo(e.target.value)} />
          {termo && <button type="button" onClick={() => setTermo("")} className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground" aria-label="Limpar"><X className="size-4" /></button>}
        </div>
      </CabecalhoPagina>
      {consulta.isError && !d ? (
        <ErroCarregamento erro={consulta.error} tentarDeNovo={() => consulta.refetch()} />
      ) : !d ? (
        <SkeletonLinhas n={10} />
      ) : d.total === 0 ? (
        <Vazio titulo="Nenhuma atividade" />
      ) : (
        <div className={cn("space-y-3 transition-opacity", consulta.isFetching && "opacity-70")}>
          <ol className="divide-y rounded-xl border bg-card">
            {d.resultados.map((a) => (
              <li key={a.id} className="flex gap-3 px-4 py-3 text-sm">
                <span className="mt-1.5 size-2 shrink-0 rounded-full bg-primary/70" />
                <div className="min-w-0 flex-1">
                  <div>
                    <span className="font-medium">{a.usuario?.nome ?? "Sistema"}</span> {a.verbo}{" "}
                    {a.alvo && (a.url ? <a href={a.url} className="underline-offset-2 hover:underline">{a.alvo}</a> : <span>{a.alvo}</span>)}
                  </div>
                  {a.descricao && <div className="text-xs text-muted-foreground">{a.descricao}</div>}
                </div>
                <span className="shrink-0 text-xs text-muted-foreground" title={dataHora(a.criado_em)}>{relativo(a.criado_em)}</span>
              </li>
            ))}
          </ol>
          <Paginacao pagina={d.pagina} paginas={d.paginas} total={d.total} rotulo="atividades" aoMudar={(p) => void navigate({ search: (s) => ({ ...s, pagina: p === 1 ? undefined : p }), replace: true })} />
        </div>
      )}
    </div>
  );
}
