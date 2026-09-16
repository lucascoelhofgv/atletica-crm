import { useMutation, useQueryClient } from "@tanstack/react-query";
import { createFileRoute, useRouter } from "@tanstack/react-router";
import { toast } from "sonner";

import { CabecalhoPagina } from "@/app/CabecalhoPagina";
import { aplicarErrosApi } from "@/components/formulario";
import { chaves, criarEvento } from "@/features/eventos/api";
import { EventoForm } from "@/features/eventos/components/EventoForm";

export const Route = createFileRoute("/_auth/eventos/novo")({
  component: PaginaNovoEvento,
});

function PaginaNovoEvento() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const criar = useMutation({ mutationFn: criarEvento });

  return (
    <div className="mx-auto max-w-3xl space-y-4">
      <CabecalhoPagina titulo="Novo evento" voltar={{ para: "/eventos", rotulo: "Eventos" }} />
      <EventoForm
        salvando={criar.isPending}
        rotuloSalvar="Criar evento"
        aoCancelar={() => router.history.back()}
        aoSalvar={(dados, form) =>
          criar.mutate(dados, {
            onSuccess: (e) => {
              void queryClient.invalidateQueries({ queryKey: chaves.todos });
              void queryClient.invalidateQueries({ queryKey: ["dashboard"] });
              toast.success("Evento criado. Agora cadastre lotes, custos e receitas.");
              void router.navigate({ to: "/eventos/$id", params: { id: String(e.id) } });
            },
            onError: (erro) => aplicarErrosApi(form, erro),
          })
        }
      />
    </div>
  );
}
