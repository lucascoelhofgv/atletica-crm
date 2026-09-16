import { useMutation, useQueryClient, useSuspenseQuery } from "@tanstack/react-query";
import { createFileRoute, useRouter } from "@tanstack/react-router";
import { toast } from "sonner";

import { CabecalhoPagina } from "@/app/CabecalhoPagina";
import { PaginaCarregando } from "@/components/estado";
import { aplicarErrosApi } from "@/components/formulario";
import { atualizarTarefa, chaves, tarefaQuery } from "@/features/tarefas/api";
import { TarefaForm } from "@/features/tarefas/components/TarefaForm";
import type { TarefaEntrada } from "@/features/tarefas/types";

export const Route = createFileRoute("/_auth/tarefas/$id/editar")({
  loader: ({ context, params }) => context.queryClient.ensureQueryData(tarefaQuery(Number(params.id))),
  pendingComponent: PaginaCarregando,
  component: PaginaEditarTarefa,
});

function PaginaEditarTarefa() {
  const { id } = Route.useParams();
  const router = useRouter();
  const queryClient = useQueryClient();
  const { data: t } = useSuspenseQuery(tarefaQuery(Number(id)));
  const salvar = useMutation({ mutationFn: (d: Partial<TarefaEntrada>) => atualizarTarefa(t.id, d) });

  return (
    <div className="mx-auto max-w-3xl space-y-4">
      <CabecalhoPagina titulo={`Editar: ${t.titulo}`} voltar={{ para: "/tarefas", rotulo: "Tarefas" }} />
      <TarefaForm
        inicial={t}
        salvando={salvar.isPending}
        aoCancelar={() => router.history.back()}
        aoSalvar={(dados, form) =>
          salvar.mutate(dados, {
            onSuccess: (nova) => {
              queryClient.setQueryData(chaves.detalhe(nova.id), nova);
              void queryClient.invalidateQueries({ queryKey: chaves.todos });
              toast.success("Tarefa atualizada.");
              void router.navigate({ to: "/tarefas/$id", params: { id: String(nova.id) } });
            },
            onError: (erro) => aplicarErrosApi(form, erro),
          })
        }
      />
    </div>
  );
}
