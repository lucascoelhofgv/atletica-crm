import { useMutation, useQueryClient } from "@tanstack/react-query";
import { createFileRoute, useRouter } from "@tanstack/react-router";
import { toast } from "sonner";

import { CabecalhoPagina } from "@/app/CabecalhoPagina";
import { aplicarErrosApi } from "@/components/formulario";
import { chaves, criarPedido } from "@/features/pedidos/api";
import { PedidoForm } from "@/features/pedidos/components/PedidoForm";

export const Route = createFileRoute("/_auth/pedidos/novo")({
  component: PaginaNovoPedido,
});

function PaginaNovoPedido() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const criar = useMutation({ mutationFn: criarPedido });

  return (
    <div className="mx-auto max-w-4xl space-y-4">
      <CabecalhoPagina titulo="Novo pedido" voltar={{ para: "/pedidos", rotulo: "Pedidos" }} />
      <PedidoForm
        salvando={criar.isPending}
        rotuloSalvar="Salvar pedido"
        aoCancelar={() => router.history.back()}
        aoSalvar={(dados, form) =>
          criar.mutate(dados, {
            onSuccess: (pedido) => {
              void queryClient.invalidateQueries({ queryKey: chaves.todos });
              void queryClient.invalidateQueries({ queryKey: ["produtos"] });
              void queryClient.invalidateQueries({ queryKey: ["dashboard"] });
              toast.success(pedido.numero ? `Pedido ${pedido.numero} salvo.` : "Rascunho salvo.");
              void router.navigate({ to: "/pedidos/$id", params: { id: String(pedido.id) } });
            },
            onError: (erro) => aplicarErrosApi(form, erro),
          })
        }
      />
    </div>
  );
}
