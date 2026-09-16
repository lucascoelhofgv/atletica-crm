import { useMutation, useQueryClient, useSuspenseQuery } from "@tanstack/react-query";
import { createFileRoute, useRouter } from "@tanstack/react-router";
import { toast } from "sonner";

import { CabecalhoPagina } from "@/app/CabecalhoPagina";
import { PaginaCarregando } from "@/components/estado";
import { aplicarErrosApi } from "@/components/formulario";
import { atualizarFornecedor, chaves, fornecedorQuery } from "@/features/fornecedores/api";
import { FornecedorForm } from "@/features/fornecedores/components/FornecedorForm";
import type { FornecedorEntrada } from "@/features/fornecedores/types";

export const Route = createFileRoute("/_auth/fornecedores/$id/editar")({
  loader: ({ context, params }) => context.queryClient.ensureQueryData(fornecedorQuery(Number(params.id))),
  pendingComponent: PaginaCarregando,
  component: PaginaEditarFornecedor,
});

function PaginaEditarFornecedor() {
  const { id } = Route.useParams();
  const router = useRouter();
  const queryClient = useQueryClient();
  const { data: f } = useSuspenseQuery(fornecedorQuery(Number(id)));
  const salvar = useMutation({ mutationFn: (d: Partial<FornecedorEntrada>) => atualizarFornecedor(f.id, d) });

  return (
    <div className="mx-auto max-w-3xl space-y-4">
      <CabecalhoPagina titulo={`Editar ${f.nome_exibicao}`} voltar={{ para: "/fornecedores", rotulo: "Fornecedores" }} />
      <FornecedorForm
        inicial={f}
        salvando={salvar.isPending}
        aoCancelar={() => router.history.back()}
        aoSalvar={(dados, form) =>
          salvar.mutate(dados, {
            onSuccess: (novo) => {
              queryClient.setQueryData(chaves.detalhe(novo.id), novo);
              void queryClient.invalidateQueries({ queryKey: chaves.todos });
              toast.success("Fornecedor atualizado.");
              void router.navigate({ to: "/fornecedores/$id", params: { id: String(novo.id) } });
            },
            onError: (erro) => aplicarErrosApi(form, erro),
          })
        }
      />
    </div>
  );
}
