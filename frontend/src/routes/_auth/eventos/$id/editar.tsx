import { useMutation, useQueryClient, useSuspenseQuery } from "@tanstack/react-query";
import { createFileRoute, useRouter } from "@tanstack/react-router";
import { toast } from "sonner";

import { CabecalhoPagina } from "@/app/CabecalhoPagina";
import { PaginaCarregando } from "@/components/estado";
import { aplicarErrosApi } from "@/components/formulario";
import { atualizarEvento, chaves, eventoQuery } from "@/features/eventos/api";
import { EventoForm } from "@/features/eventos/components/EventoForm";
import type { EventoEntrada } from "@/features/eventos/types";

export const Route = createFileRoute("/_auth/eventos/$id/editar")({
  loader: ({ context, params }) => context.queryClient.ensureQueryData(eventoQuery(Number(params.id))),
  pendingComponent: PaginaCarregando,
  component: PaginaEditarEvento,
});

function PaginaEditarEvento() {
  const { id } = Route.useParams();
  const router = useRouter();
  const queryClient = useQueryClient();
  const { data: e } = useSuspenseQuery(eventoQuery(Number(id)));
  const salvar = useMutation({ mutationFn: (d: Partial<EventoEntrada>) => atualizarEvento(e.id, d) });

  return (
    <div className="mx-auto max-w-3xl space-y-4">
      <CabecalhoPagina titulo={`Editar ${e.nome}`} voltar={{ para: "/eventos", rotulo: "Eventos" }} />
      <EventoForm
        inicial={e}
        salvando={salvar.isPending}
        aoCancelar={() => router.history.back()}
        aoSalvar={(dados, form) =>
          salvar.mutate(dados, {
            onSuccess: (novo) => {
              queryClient.setQueryData(chaves.detalhe(novo.id), novo);
              void queryClient.invalidateQueries({ queryKey: chaves.todos });
              toast.success("Evento atualizado.");
              void router.navigate({ to: "/eventos/$id", params: { id: String(novo.id) } });
            },
            onError: (erro) => aplicarErrosApi(form, erro),
          })
        }
      />
    </div>
  );
}
