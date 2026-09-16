import { useMutation, useQueryClient } from "@tanstack/react-query";
import { createFileRoute, useRouter } from "@tanstack/react-router";
import { toast } from "sonner";

import { CabecalhoPagina } from "@/app/CabecalhoPagina";
import { aplicarErrosApi } from "@/components/formulario";
import { chaves, criarProduto } from "@/features/produtos/api";
import { ProdutoForm } from "@/features/produtos/components/ProdutoForm";
import type { ProdutoEntrada } from "@/features/produtos/types";

export const Route = createFileRoute("/_auth/produtos/novo")({
  component: PaginaNovoProduto,
});

function PaginaNovoProduto() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const criar = useMutation({
    mutationFn: ({ dados, foto }: { dados: ProdutoEntrada; foto?: File | null }) => criarProduto(dados, foto),
  });

  return (
    <div className="mx-auto max-w-3xl space-y-4">
      <CabecalhoPagina titulo="Novo produto" voltar={{ para: "/produtos", rotulo: "Produtos" }} />
      <ProdutoForm
        salvando={criar.isPending}
        rotuloSalvar="Cadastrar"
        aoCancelar={() => router.history.back()}
        aoSalvar={(dados, foto, form) =>
          criar.mutate({ dados, foto }, {
            onSuccess: (produto) => {
              void queryClient.invalidateQueries({ queryKey: chaves.todos });
              toast.success("Produto cadastrado. Registre a entrada inicial de estoque.");
              void router.navigate({ to: "/produtos/$id", params: { id: String(produto.id) } });
            },
            onError: (erro) => aplicarErrosApi(form, erro),
          })
        }
      />
    </div>
  );
}
