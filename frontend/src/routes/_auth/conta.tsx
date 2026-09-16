import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { createFileRoute } from "@tanstack/react-router";
import { LoaderCircle } from "lucide-react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";

import { CabecalhoPagina } from "@/app/CabecalhoPagina";
import { aplicarErrosApi, Campo, Secao } from "@/components/formulario";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { alterarSenha } from "@/features/auth/api";
import { usuarioAtualQuery, useUsuario } from "@/features/auth/queries";
import type { Usuario } from "@/features/auth/types";
import { api } from "@/lib/api";
import { iniciais } from "@/lib/formatos";

export const Route = createFileRoute("/_auth/conta")({
  component: PaginaConta,
});

const esquemaDados = z.object({
  first_name: z.string().trim(),
  last_name: z.string().trim(),
  email: z.string().trim().email("E-mail inválido"),
  telefone: z.string().trim(),
});
const esquemaSenha = z
  .object({
    senha_atual: z.string().min(1, "Informe a senha atual"),
    senha_nova: z.string().min(8, "Mínimo 8 caracteres"),
    senha_nova_confirmacao: z.string(),
  })
  .refine((v) => v.senha_nova === v.senha_nova_confirmacao, { path: ["senha_nova_confirmacao"], message: "As senhas não conferem" });

function PaginaConta() {
  const usuario = useUsuario();
  const queryClient = useQueryClient();
  const partes = usuario.nome.split(" ");

  const formDados = useForm<z.infer<typeof esquemaDados>>({
    resolver: zodResolver(esquemaDados),
    defaultValues: { first_name: partes[0] === usuario.username ? "" : partes[0] ?? "", last_name: partes.slice(1).join(" "), email: usuario.email, telefone: "" },
  });
  const salvarDados = useMutation({
    mutationFn: (v: z.infer<typeof esquemaDados>) => api<Usuario>("auth/me/", { method: "PATCH", body: v }),
    onSuccess: (u) => { queryClient.setQueryData(usuarioAtualQuery.queryKey, u); toast.success("Dados atualizados."); },
    onError: (e) => aplicarErrosApi(formDados, e),
  });
  const foto = useMutation({
    mutationFn: (arquivo: File) => { const fd = new FormData(); fd.append("foto", arquivo); return api<Usuario>("auth/me/", { method: "PATCH", body: fd }); },
    onSuccess: (u) => { queryClient.setQueryData(usuarioAtualQuery.queryKey, u); toast.success("Foto atualizada."); },
    onError: (e: Error) => toast.error(e.message),
  });

  const formSenha = useForm<z.infer<typeof esquemaSenha>>({ resolver: zodResolver(esquemaSenha), defaultValues: { senha_atual: "", senha_nova: "", senha_nova_confirmacao: "" } });
  const trocarSenha = useMutation({
    mutationFn: alterarSenha,
    onSuccess: () => { toast.success("Senha alterada."); formSenha.reset(); },
    onError: (e) => aplicarErrosApi(formSenha, e),
  });
  const e1 = formDados.formState.errors;
  const e2 = formSenha.formState.errors;

  return (
    <div className="mx-auto max-w-3xl space-y-4">
      <CabecalhoPagina titulo="Minha conta" descricao={<span className="flex items-center gap-2"><Badge variant="secondary" className="font-normal">{usuario.perfil_principal}</Badge>{usuario.cargo && <span className="text-xs">{usuario.cargo}</span>}</span>} />

      <form noValidate onSubmit={formDados.handleSubmit((v) => salvarDados.mutate(v))} className="space-y-4">
        <Secao titulo="Meus dados">
          <div className="flex items-center gap-4 sm:col-span-2">
            <Avatar className="size-16">{usuario.foto && <AvatarImage src={usuario.foto} alt="" />}<AvatarFallback className="text-lg">{iniciais(usuario.nome)}</AvatarFallback></Avatar>
            <label className="cursor-pointer text-sm text-muted-foreground hover:text-foreground">
              {foto.isPending ? "enviando…" : "Trocar foto"}
              <input type="file" accept="image/*" className="hidden" onChange={(ev) => ev.target.files?.[0] && foto.mutate(ev.target.files[0])} />
            </label>
          </div>
          <Campo id="first_name" rotulo="Nome" erro={e1.first_name?.message}><Input id="first_name" {...formDados.register("first_name")} /></Campo>
          <Campo id="last_name" rotulo="Sobrenome" erro={e1.last_name?.message}><Input id="last_name" {...formDados.register("last_name")} /></Campo>
          <Campo id="email" rotulo="E-mail" obrigatorio erro={e1.email?.message}><Input id="email" type="email" {...formDados.register("email")} aria-invalid={!!e1.email} /></Campo>
          <Campo id="telefone" rotulo="Telefone" erro={e1.telefone?.message}><Input id="telefone" {...formDados.register("telefone")} /></Campo>
          <div className="flex justify-end sm:col-span-2"><Button type="submit" disabled={salvarDados.isPending}>{salvarDados.isPending && <LoaderCircle className="animate-spin" />} Salvar dados</Button></div>
        </Secao>
      </form>

      <form noValidate onSubmit={formSenha.handleSubmit((v) => trocarSenha.mutate(v))} className="space-y-4">
        <Secao titulo="Alterar senha" descricao="Mínimo 8 caracteres, não só números, diferente do usuário.">
          <Campo id="senha_atual" rotulo="Senha atual" obrigatorio erro={e2.senha_atual?.message} className="sm:col-span-2"><Input id="senha_atual" type="password" autoComplete="current-password" {...formSenha.register("senha_atual")} aria-invalid={!!e2.senha_atual} /></Campo>
          <Campo id="senha_nova" rotulo="Nova senha" obrigatorio erro={e2.senha_nova?.message}><Input id="senha_nova" type="password" autoComplete="new-password" {...formSenha.register("senha_nova")} aria-invalid={!!e2.senha_nova} /></Campo>
          <Campo id="senha_nova_confirmacao" rotulo="Confirmar nova senha" obrigatorio erro={e2.senha_nova_confirmacao?.message}><Input id="senha_nova_confirmacao" type="password" autoComplete="new-password" {...formSenha.register("senha_nova_confirmacao")} aria-invalid={!!e2.senha_nova_confirmacao} /></Campo>
          <div className="flex justify-end sm:col-span-2"><Button type="submit" variant="outline" disabled={trocarSenha.isPending}>{trocarSenha.isPending && <LoaderCircle className="animate-spin" />} Alterar senha</Button></div>
        </Secao>
      </form>
    </div>
  );
}
