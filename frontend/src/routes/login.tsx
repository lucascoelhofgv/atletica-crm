import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { createFileRoute, redirect, useRouter } from "@tanstack/react-router";
import { Eye, EyeOff, LoaderCircle } from "lucide-react";
import { motion, useReducedMotion } from "motion/react";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { Marca } from "@/app/Marca";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { login } from "@/features/auth/api";
import { usuarioAtualQuery } from "@/features/auth/queries";
import { configQuery } from "@/features/config/api";
import { ApiErro } from "@/lib/api";

const esquema = z.object({
  usuario: z.string().trim().min(1, "Informe seu usuário ou e-mail"),
  senha: z.string().min(1, "Informe sua senha"),
});
type Formulario = z.infer<typeof esquema>;

export const Route = createFileRoute("/login")({
  validateSearch: (busca: Record<string, unknown>) => ({
    voltar: typeof busca.voltar === "string" ? busca.voltar : undefined,
  }),
  beforeLoad: async ({ context }) => {
    const usuario = await context.queryClient.ensureQueryData(usuarioAtualQuery);
    if (usuario) throw redirect({ to: "/" });
  },
  component: PaginaLogin,
});

function PaginaLogin() {
  const { voltar } = Route.useSearch();
  const router = useRouter();
  const queryClient = useQueryClient();
  const { data: cfg } = useQuery(configQuery);
  const [mostrarSenha, setMostrarSenha] = useState(false);
  const reduzirMovimento = useReducedMotion();

  const form = useForm<Formulario>({
    resolver: zodResolver(esquema),
    defaultValues: { usuario: "", senha: "" },
  });

  const entrar = useMutation({
    mutationFn: login,
    onSuccess: (usuario) => {
      queryClient.setQueryData(usuarioAtualQuery.queryKey, usuario);
      if (voltar && voltar.startsWith("/")) router.history.push(voltar);
      else router.navigate({ to: "/" });
    },
    onError: (erro) => {
      const mensagem = erro instanceof ApiErro ? erro.message : "Não foi possível entrar.";
      form.setError("root", { message: mensagem });
    },
  });

  return (
    <div className="relative flex min-h-dvh items-center justify-center overflow-hidden px-4 py-10">
      {/* Fundo: gradiente discreto com as cores da marca. */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 -z-10 opacity-70"
        style={{
          background:
            "radial-gradient(60% 50% at 20% 10%, color-mix(in oklch, var(--brand-primary) 45%, transparent), transparent 70%)," +
            "radial-gradient(50% 40% at 90% 90%, color-mix(in oklch, var(--brand-secondary) 25%, transparent), transparent 70%)",
        }}
      />

      <motion.div
        initial={reduzirMovimento ? false : { opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.35, ease: "easeOut" }}
        className="w-full max-w-sm rounded-2xl border bg-card/95 p-6 shadow-xl backdrop-blur sm:p-8"
      >
        <Marca className="mb-6" />

        <h1 className="font-display text-xl font-semibold">Entrar</h1>
        <p className="mb-6 text-sm text-muted-foreground">
          Acesse o {cfg?.titulo_app ?? "CRM"} com seu usuário ou e-mail.
        </p>

        <form
          className="space-y-4"
          onSubmit={form.handleSubmit((dados) => entrar.mutate(dados))}
          noValidate
        >
          <div className="space-y-1.5">
            <Label htmlFor="usuario">Usuário ou e-mail</Label>
            <Input
              id="usuario"
              autoComplete="username"
              autoFocus
              aria-invalid={!!form.formState.errors.usuario}
              {...form.register("usuario")}
            />
            <MensagemCampo texto={form.formState.errors.usuario?.message} />
          </div>

          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <Label htmlFor="senha">Senha</Label>
              <a
                href="/conta/senha/"
                className="text-xs text-muted-foreground underline-offset-4 hover:text-foreground hover:underline"
              >
                Esqueci minha senha
              </a>
            </div>
            <div className="relative">
              <Input
                id="senha"
                type={mostrarSenha ? "text" : "password"}
                autoComplete="current-password"
                className="pr-10"
                aria-invalid={!!form.formState.errors.senha}
                {...form.register("senha")}
              />
              <button
                type="button"
                onClick={() => setMostrarSenha((v) => !v)}
                className="absolute inset-y-0 right-0 flex w-10 items-center justify-center text-muted-foreground hover:text-foreground"
                aria-label={mostrarSenha ? "Ocultar senha" : "Mostrar senha"}
              >
                {mostrarSenha ? <EyeOff className="size-4" /> : <Eye className="size-4" />}
              </button>
            </div>
            <MensagemCampo texto={form.formState.errors.senha?.message} />
          </div>

          {form.formState.errors.root && (
            <div
              role="alert"
              className="rounded-lg border border-destructive/40 bg-destructive/10 px-3 py-2 text-sm text-destructive"
            >
              {form.formState.errors.root.message}
            </div>
          )}

          <Button type="submit" className="w-full" disabled={entrar.isPending}>
            {entrar.isPending && <LoaderCircle className="animate-spin" />}
            {entrar.isPending ? "Entrando…" : "Entrar"}
          </Button>
        </form>
      </motion.div>
    </div>
  );
}

function MensagemCampo({ texto }: { texto?: string }) {
  if (!texto) return null;
  return <p className="text-xs text-destructive">{texto}</p>;
}
