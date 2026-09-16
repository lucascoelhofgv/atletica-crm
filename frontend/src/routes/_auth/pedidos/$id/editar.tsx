import { useMutation, useQueryClient, useSuspenseQuery } from "@tanstack/react-query";
import { createFileRoute, useRouter } from "@tanstack/react-router";
import { toast } from "sonner";

import { CabecalhoPagina } from "@/app/CabecalhoPagina";
import { PaginaCarregando } from "@/components/estado";
import { aplicarErrosApi } from "@/components/formulario";
import { atualizarPedido, chaves, pedidoQuery } from "@/features/pedidos/api";
import { PedidoForm } from "@/features/pedidos/components/PedidoForm";
import type { PedidoEntrada } from "@/features/pedidos/types";

export const Route = createFileRoute("/_auth/pedidos/$id/editar")({
  loader: ({ context, params }) => context.queryClient.ensureQueryData(pedidoQuery(Number(params.id))),
  pendingComponent: PaginaCarregando,
  component: PaginaEditarPedido,
});

function PaginaEditarPedido() {
  const { id } = Route.useParams();
  const router = useRouter();
  const queryClient = useQueryClient();
  const { data: pedido } = useSuspenseQuery(pedidoQuery(Number(id)));
  const salvar = useMutation({ mutationFn: (dados: PedidoEntrada) => atualizarPedido(pedido.id, dados) });

  return (
    <div className="mx-auto max-w-4xl space-y-4">
      <CabecalhoPagina
        titulo={`Editar ${pedido.numero || `rascunho #${pedido.id}`}`}
        descricao={pedido.estoque_baixado ? "Este pedido já baixou estoque: alterar itens estorna os antigos e baixa os novos." : undefined}
        voltar={{ para: "/pedidos", rotulo: "Pedidos" }}
      />
      <PedidoForm
        inicial={pedido}
        salvando={salvar.isPending}
        aoCancelar={() => router.history.back()}
        aoSalvar={(dados, form) =>
          salvar.mutate(dados, {
            onSuccess: (atualizado) => {
              queryClient.setQueryData(chaves.detalhe(atualizado.id), atualizado);
              void queryClient.invalidateQueries({ queryKey: chaves.todos });
              void queryClient.invalidateQueries({ queryKey: ["produtos"] });
              void queryClient.invalidateQueries({ queryKey: ["dashboard"] });
              toast.success("Pedido atualizado.");
              void router.navigate({ to: "/pedidos/$id", params: { id: String(atualizado.id) } });
            },
            onError: (erro) => aplicarErrosApi(form, erro),
          })
        }
      />
    </div>
  );
}
