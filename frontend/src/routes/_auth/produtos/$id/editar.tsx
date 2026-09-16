import { useMutation, useQueryClient, useSuspenseQuery } from "@tanstack/react-query";
import { createFileRoute, useRouter } from "@tanstack/react-router";
import { toast } from "sonner";

import { CabecalhoPagina } from "@/app/CabecalhoPagina";
import { PaginaCarregando } from "@/components/estado";
import { aplicarErrosApi } from "@/components/formulario";
import { atualizarProduto, chaves, produtoQuery } from "@/features/produtos/api";
import { ProdutoForm } from "@/features/produtos/components/ProdutoForm";
import type { ProdutoEntrada } from "@/features/produtos/types";

export const Route = createFileRoute("/_auth/produtos/$id/editar")({
  loader: ({ context, params }) => context.queryClient.ensureQueryData(produtoQuery(Number(params.id))),
  pendingComponent: PaginaCarregando,
  component: PaginaEditarProduto,
});

function PaginaEditarProduto() {
  const { id } = Route.useParams();
  const router = useRouter();
  const queryClient = useQueryClient();
  const { data: produto } = useSuspenseQuery(produtoQuery(Number(id)));
  const salvar = useMutation({
    mutationFn: ({ dados, foto }: { dados: Partial<ProdutoEntrada>; foto?: File | null }) => atualizarProduto(produto.id, dados, foto),
  });

  return (
    <div className="mx-auto max-w-3xl space-y-4">
      <CabecalhoPagina titulo={`Editar ${produto.nome_completo}`} voltar={{ para: "/produtos", rotulo: "Produtos" }} />
      <ProdutoForm
        inicial={produto}
        salvando={salvar.isPending}
        aoCancelar={() => router.history.back()}
        aoSalvar={(dados, foto, form) =>
          salvar.mutate({ dados, foto }, {
            onSuccess: (atualizado) => {
              queryClient.setQueryData(chaves.detalhe(atualizado.id), atualizado);
              void queryClient.invalidateQueries({ queryKey: chaves.todos });
              toast.success("Produto atualizado.");
              void router.navigate({ to: "/produtos/$id", params: { id: String(atualizado.id) } });
            },
            onError: (erro) => aplicarErrosApi(form, erro),
          })
        }
      />
    </div>
  );
}
