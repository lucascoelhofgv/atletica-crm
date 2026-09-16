import { useMutation, useQueryClient } from "@tanstack/react-query";
import { createFileRoute, useRouter } from "@tanstack/react-router";
import { toast } from "sonner";

import { CabecalhoPagina } from "@/app/CabecalhoPagina";
import { aplicarErrosApi } from "@/components/formulario";
import { useUsuario } from "@/features/auth/queries";
import { chaves, criarTarefa } from "@/features/tarefas/api";
import { TarefaForm } from "@/features/tarefas/components/TarefaForm";

export const Route = createFileRoute("/_auth/tarefas/nova")({
  component: PaginaNovaTarefa,
});

function PaginaNovaTarefa() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const usuario = useUsuario();
  const criar = useMutation({ mutationFn: criarTarefa });

  return (
    <div className="mx-auto max-w-3xl space-y-4">
      <CabecalhoPagina titulo="Nova tarefa" voltar={{ para: "/tarefas", rotulo: "Tarefas" }} />
      <TarefaForm
        responsavelPadrao={usuario.id}
        salvando={criar.isPending}
        rotuloSalvar="Criar tarefa"
        aoCancelar={() => router.history.back()}
        aoSalvar={(dados, form) =>
          criar.mutate(dados, {
            onSuccess: () => {
              void queryClient.invalidateQueries({ queryKey: chaves.todos });
              void queryClient.invalidateQueries({ queryKey: ["dashboard"] });
              toast.success("Tarefa criada.");
              void router.navigate({ to: "/tarefas", search: {} });
            },
            onError: (erro) => aplicarErrosApi(form, erro),
          })
        }
      />
    </div>
  );
}
