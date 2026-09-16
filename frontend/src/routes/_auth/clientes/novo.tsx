import { useMutation, useQueryClient } from "@tanstack/react-query";
import { createFileRoute, useRouter } from "@tanstack/react-router";
import { toast } from "sonner";

import { CabecalhoPagina } from "@/app/CabecalhoPagina";
import { aplicarErrosApi } from "@/components/formulario";
import { chaves, criarCliente } from "@/features/clientes/api";
import { ClienteForm } from "@/features/clientes/components/ClienteForm";

export const Route = createFileRoute("/_auth/clientes/novo")({
  component: PaginaNovoCliente,
});

function PaginaNovoCliente() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const criar = useMutation({ mutationFn: criarCliente });

  return (
    <div className="mx-auto max-w-3xl space-y-4">
      <CabecalhoPagina titulo="Novo cliente" voltar={{ para: "/clientes", rotulo: "Clientes" }} />
      <ClienteForm
        salvando={criar.isPending}
        rotuloSalvar="Cadastrar"
        aoCancelar={() => router.history.back()}
        aoSalvar={(dados, form) =>
          criar.mutate(dados, {
            onSuccess: (cliente) => {
              void queryClient.invalidateQueries({ queryKey: chaves.todos });
              toast.success("Cliente cadastrado.");
              void router.navigate({ to: "/clientes/$id", params: { id: String(cliente.id) } });
            },
            onError: (erro) => aplicarErrosApi(form, erro),
          })
        }
      />
    </div>
  );
}
