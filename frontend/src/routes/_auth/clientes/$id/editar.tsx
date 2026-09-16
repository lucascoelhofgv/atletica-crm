import { useMutation, useQueryClient, useSuspenseQuery } from "@tanstack/react-query";
import { createFileRoute, useRouter } from "@tanstack/react-router";
import { toast } from "sonner";

import { CabecalhoPagina } from "@/app/CabecalhoPagina";
import { PaginaCarregando } from "@/components/estado";
import { aplicarErrosApi } from "@/components/formulario";
import { atualizarCliente, chaves, clienteQuery } from "@/features/clientes/api";
import { ClienteForm } from "@/features/clientes/components/ClienteForm";

export const Route = createFileRoute("/_auth/clientes/$id/editar")({
  loader: ({ context, params }) => context.queryClient.ensureQueryData(clienteQuery(Number(params.id))),
  pendingComponent: PaginaCarregando,
  component: PaginaEditarCliente,
});

function PaginaEditarCliente() {
  const { id } = Route.useParams();
  const router = useRouter();
  const queryClient = useQueryClient();
  const { data: cliente } = useSuspenseQuery(clienteQuery(Number(id)));
  const salvar = useMutation({ mutationFn: (dados: Parameters<typeof atualizarCliente>[1]) => atualizarCliente(cliente.id, dados) });

  return (
    <div className="mx-auto max-w-3xl space-y-4">
      <CabecalhoPagina titulo={`Editar ${cliente.nome_social || cliente.nome}`} voltar={{ para: "/clientes", rotulo: "Clientes" }} />
      <ClienteForm
        inicial={cliente}
        salvando={salvar.isPending}
        aoCancelar={() => router.history.back()}
        aoSalvar={(dados, form) =>
          salvar.mutate(dados, {
            onSuccess: (atualizado) => {
              queryClient.setQueryData(chaves.detalhe(atualizado.id), atualizado);
              void queryClient.invalidateQueries({ queryKey: chaves.todos });
              toast.success("Cliente atualizado.");
              void router.navigate({ to: "/clientes/$id", params: { id: String(atualizado.id) } });
            },
            onError: (erro) => aplicarErrosApi(form, erro),
          })
        }
      />
    </div>
  );
}
