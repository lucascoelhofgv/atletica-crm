import { useMutation, useQueryClient } from "@tanstack/react-query";
import { createFileRoute, useRouter } from "@tanstack/react-router";
import { toast } from "sonner";

import { CabecalhoPagina } from "@/app/CabecalhoPagina";
import { aplicarErrosApi } from "@/components/formulario";
import { chaves, criarFornecedor } from "@/features/fornecedores/api";
import { FornecedorForm } from "@/features/fornecedores/components/FornecedorForm";

export const Route = createFileRoute("/_auth/fornecedores/novo")({
  component: PaginaNovoFornecedor,
});

function PaginaNovoFornecedor() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const criar = useMutation({ mutationFn: criarFornecedor });

  return (
    <div className="mx-auto max-w-3xl space-y-4">
      <CabecalhoPagina titulo="Novo fornecedor" voltar={{ para: "/fornecedores", rotulo: "Fornecedores" }} />
      <FornecedorForm
        salvando={criar.isPending}
        rotuloSalvar="Cadastrar"
        aoCancelar={() => router.history.back()}
        aoSalvar={(dados, form) =>
          criar.mutate(dados, {
            onSuccess: (f) => {
              void queryClient.invalidateQueries({ queryKey: chaves.todos });
              toast.success("Fornecedor cadastrado.");
              void router.navigate({ to: "/fornecedores/$id", params: { id: String(f.id) } });
            },
            onError: (erro) => aplicarErrosApi(form, erro),
          })
        }
      />
    </div>
  );
}
