import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { createFileRoute } from "@tanstack/react-router";
import { LoaderCircle, Pencil, Plus, Search, UserRoundX, UserRoundCheck, X } from "lucide-react";
import { useEffect, useState } from "react";
import { Controller, useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";

import { CabecalhoPagina } from "@/app/CabecalhoPagina";
import { ErroCarregamento, SkeletonLinhas, Vazio } from "@/components/estado";
import { aplicarErrosApi, Campo } from "@/components/formulario";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Textarea } from "@/components/ui/textarea";
import { usePermissao, useUsuario } from "@/features/auth/queries";
import { alternarMembro, atualizarMembro, chaves, criarMembro, membrosQuery, opcoesMembroQuery, type Membro, type MembroEntrada } from "@/features/membros/api";
import { data as fmtData, iniciais, relativo } from "@/lib/formatos";
import { cn } from "@/lib/utils";

const buscaSchema = z.object({
  q: z.string().optional().catch(undefined),
  inativos: z.boolean().optional().catch(undefined),
});

export const Route = createFileRoute("/_auth/administracao/membros")({
  validateSearch: buscaSchema,
  component: PaginaMembros,
});

const esquema = z.object({
  username: z.string().trim().min(2, "Informe o usuário").regex(/^[\w.@+-]+$/, "Só letras, números e . @ + - _"),
  first_name: z.string().trim(),
  last_name: z.string().trim(),
  email: z.string().trim().email("E-mail inválido"),
  cargo: z.string().trim(),
  telefone: z.string().trim(),
  data_entrada: z.string(),
  data_saida: z.string(),
  observacoes: z.string(),
  is_active: z.boolean(),
  grupos_ids: z.array(z.number()),
  senha: z.string(),
});
type Valores = z.infer<typeof esquema>;

function FormularioMembro({ membro, aberto, aoFechar }: { membro: Membro | null; aberto: boolean; aoFechar: () => void }) {
  const queryClient = useQueryClient();
  const { data: opcoes } = useQuery(opcoesMembroQuery);
  const novo = membro === null;
  const form = useForm<Valores>({
    resolver: zodResolver(esquema),
    defaultValues: {
      username: membro?.username ?? "", first_name: membro?.first_name ?? "", last_name: membro?.last_name ?? "",
      email: membro?.email ?? "", cargo: membro?.cargo ?? "", telefone: membro?.telefone ?? "",
      data_entrada: membro?.data_entrada ?? "", data_saida: membro?.data_saida ?? "", observacoes: membro?.observacoes ?? "",
      is_active: membro?.is_active ?? true,
      grupos_ids: opcoes?.grupos.filter((g) => membro?.perfis.includes(g.name)).map((g) => g.id) ?? [],
      senha: "",
    },
  });
  useEffect(() => {
    if (opcoes && membro) form.setValue("grupos_ids", opcoes.grupos.filter((g) => membro.perfis.includes(g.name)).map((g) => g.id));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [opcoes, membro]);
  const salvar = useMutation({
    mutationFn: (v: Valores) => {
      const d: MembroEntrada = { ...v, data_entrada: v.data_entrada || null, data_saida: v.data_saida || null, senha: v.senha || undefined };
      return novo ? criarMembro(d) : atualizarMembro(membro.id, d);
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: chaves.todos });
      toast.success(novo ? "Membro criado." : "Membro atualizado.");
      aoFechar();
    },
    onError: (erro) => aplicarErrosApi(form, erro),
  });
  const erros = form.formState.errors;
  const r = form.register;

  return (
    <Dialog open={aberto} onOpenChange={(o) => !o && aoFechar()}>
      <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>{novo ? "Novo membro" : `Editar ${membro.nome}`}</DialogTitle>
          <DialogDescription>{novo ? "Defina usuário, senha inicial e perfis de acesso." : "Quem sai da Atlética é desativado, nunca apagado."}</DialogDescription>
        </DialogHeader>
        <form className="grid gap-4 sm:grid-cols-2" noValidate onSubmit={form.handleSubmit((v) => salvar.mutate(v))}>
          <Campo id="username" rotulo="Usuário" obrigatorio erro={erros.username?.message}><Input id="username" autoFocus={novo} autoComplete="off" {...r("username")} aria-invalid={!!erros.username} /></Campo>
          <Campo id="email" rotulo="E-mail" obrigatorio erro={erros.email?.message}><Input id="email" type="email" autoComplete="off" {...r("email")} aria-invalid={!!erros.email} /></Campo>
          <Campo id="first_name" rotulo="Nome" erro={erros.first_name?.message}><Input id="first_name" {...r("first_name")} /></Campo>
          <Campo id="last_name" rotulo="Sobrenome" erro={erros.last_name?.message}><Input id="last_name" {...r("last_name")} /></Campo>
          <Campo id="cargo" rotulo="Cargo na Atlética" erro={erros.cargo?.message}><Input id="cargo" placeholder="ex.: Diretor financeiro" {...r("cargo")} /></Campo>
          <Campo id="telefone" rotulo="Telefone" erro={erros.telefone?.message}><Input id="telefone" {...r("telefone")} /></Campo>
          <Campo id="data_entrada" rotulo="Entrada" erro={erros.data_entrada?.message}><Input id="data_entrada" type="date" {...r("data_entrada")} /></Campo>
          <Campo id="data_saida" rotulo="Saída" erro={erros.data_saida?.message}><Input id="data_saida" type="date" {...r("data_saida")} /></Campo>
          <Campo id="senha" rotulo={novo ? "Senha inicial" : "Nova senha"} obrigatorio={novo} erro={erros.senha?.message} ajuda={novo ? "Mínimo 8 caracteres; peça para trocar no primeiro acesso." : "Deixe em branco para manter."} className="sm:col-span-2">
            <Input id="senha" type="password" autoComplete="new-password" {...r("senha")} aria-invalid={!!erros.senha} />
          </Campo>
          <Campo rotulo="Perfis de acesso" className="sm:col-span-2" erro={erros.grupos_ids?.message}>
            <Controller control={form.control} name="grupos_ids" render={({ field }) => (
              <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
                {opcoes?.grupos.map((g) => (
                  <label key={g.id} className="flex cursor-pointer items-center gap-2 rounded-lg border px-3 py-2 text-sm hover:bg-accent">
                    <Checkbox checked={field.value.includes(g.id)} onCheckedChange={(v) => field.onChange(v ? [...field.value, g.id] : field.value.filter((x) => x !== g.id))} />
                    {g.name}
                  </label>
                ))}
              </div>
            )} />
          </Campo>
          <Campo id="observacoes" rotulo="Observações" className="sm:col-span-2"><Textarea id="observacoes" rows={2} {...r("observacoes")} /></Campo>
          {!novo && (
            <Controller control={form.control} name="is_active" render={({ field }) => (
              <label className="flex items-center gap-2 text-sm sm:col-span-2"><Switch checked={field.value} onCheckedChange={field.onChange} /> Acesso ativo</label>
            )} />
          )}
          <div className="flex justify-end gap-2 sm:col-span-2">
            <Button type="button" variant="ghost" onClick={aoFechar}>Cancelar</Button>
            <Button type="submit" disabled={salvar.isPending}>{salvar.isPending && <LoaderCircle className="animate-spin" />} {novo ? "Criar membro" : "Salvar"}</Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}

function PaginaMembros() {
  const filtros = Route.useSearch();
  const navigate = Route.useNavigate();
  const usuario = useUsuario();
  const permissao = usePermissao("membros");
  const queryClient = useQueryClient();
  const consulta = useQuery(membrosQuery({ q: filtros.q, is_active: filtros.inativos ? undefined : true }));
  const d = consulta.data;
  const [editando, setEditando] = useState<Membro | null | undefined>(undefined); // undefined = fechado

  const [termo, setTermo] = useState(filtros.q ?? "");
  useEffect(() => {
    const t = window.setTimeout(() => {
      if ((filtros.q ?? "") !== termo) void navigate({ search: (a) => ({ ...a, q: termo || undefined }), replace: true });
    }, 300);
    return () => window.clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [termo]);

  const alternar = useMutation({
    mutationFn: alternarMembro,
    onSuccess: (m) => { void queryClient.invalidateQueries({ queryKey: chaves.todos }); toast.success(m.is_active ? `${m.nome} reativado.` : `${m.nome} desativado.`); },
    onError: (e: Error) => toast.error(e.message),
  });

  return (
    <div className="space-y-4">
      <CabecalhoPagina
        titulo="Membros"
        descricao="Quem acessa o CRM e com qual perfil. Quem sai é desativado, o histórico fica."
        acoes={permissao.escrever ? <Button size="sm" onClick={() => setEditando(null)}><Plus /> Novo membro</Button> : undefined}
      >
        <div className="flex flex-wrap items-center gap-3">
          <div className="relative w-full max-w-xs">
            <Search className="pointer-events-none absolute left-2.5 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
            <Input placeholder="Nome, usuário ou e-mail…" className="h-8 pl-8 pr-8" value={termo} onChange={(e) => setTermo(e.target.value)} />
            {termo && <button type="button" onClick={() => setTermo("")} className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground" aria-label="Limpar"><X className="size-4" /></button>}
          </div>
          <div className="flex items-center gap-2">
            <Switch id="inativos" checked={!!filtros.inativos} onCheckedChange={(v) => void navigate({ search: (a) => ({ ...a, inativos: v || undefined }), replace: true })} />
            <Label htmlFor="inativos" className="cursor-pointer text-xs font-normal text-muted-foreground">Mostrar desativados</Label>
          </div>
        </div>
      </CabecalhoPagina>

      {consulta.isError && !d ? (
        <ErroCarregamento erro={consulta.error} tentarDeNovo={() => consulta.refetch()} />
      ) : !d ? (
        <SkeletonLinhas n={6} />
      ) : d.total === 0 ? (
        <Vazio titulo="Nenhum membro encontrado" />
      ) : (
        <div className={cn("overflow-hidden rounded-xl border bg-card transition-opacity", consulta.isFetching && "opacity-70")}>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Membro</TableHead>
                <TableHead className="hidden md:table-cell">Cargo</TableHead>
                <TableHead>Perfis</TableHead>
                <TableHead className="hidden lg:table-cell">Último acesso</TableHead>
                <TableHead>Status</TableHead>
                {permissao.escrever && <TableHead className="w-24" />}
              </TableRow>
            </TableHeader>
            <TableBody>
              {d.resultados.map((m) => (
                <TableRow key={m.id} className={cn(!m.is_active && "opacity-60")}>
                  <TableCell>
                    <div className="flex items-center gap-3">
                      <Avatar className="size-8">{m.foto && <AvatarImage src={m.foto} alt="" />}<AvatarFallback className="text-xs">{iniciais(m.nome)}</AvatarFallback></Avatar>
                      <div className="min-w-0">
                        <div className="font-medium">{m.nome}{m.id === usuario.id && <span className="ml-1 text-xs text-muted-foreground">(você)</span>}</div>
                        <div className="truncate text-xs text-muted-foreground">{m.username} · {m.email}</div>
                      </div>
                    </div>
                  </TableCell>
                  <TableCell className="hidden text-muted-foreground md:table-cell">{m.cargo || "—"}</TableCell>
                  <TableCell>
                    <div className="flex flex-wrap gap-1">
                      {m.is_superuser && <Badge className="font-normal">Superusuário</Badge>}
                      {m.perfis.map((p) => <Badge key={p} variant="secondary" className="font-normal">{p}</Badge>)}
                      {m.perfis.length === 0 && !m.is_superuser && <span className="text-xs text-muted-foreground">sem perfil</span>}
                    </div>
                  </TableCell>
                  <TableCell className="hidden text-muted-foreground lg:table-cell">{m.last_login ? relativo(m.last_login) : "nunca"}</TableCell>
                  <TableCell>
                    <Badge variant={m.is_active ? "secondary" : "outline"} className={cn("font-normal", m.is_active && "bg-success/15 text-success")}>{m.is_active ? "Ativo" : `Desativado${m.data_saida ? ` em ${fmtData(m.data_saida)}` : ""}`}</Badge>
                  </TableCell>
                  {permissao.escrever && (
                    <TableCell>
                      <div className="flex justify-end gap-1">
                        <Button variant="ghost" size="icon-sm" onClick={() => setEditando(m)} aria-label="Editar"><Pencil /></Button>
                        {m.id !== usuario.id && (
                          <Button variant="ghost" size="icon-sm" onClick={() => alternar.mutate(m.id)} aria-label={m.is_active ? "Desativar" : "Reativar"} className={m.is_active ? "text-muted-foreground hover:text-destructive" : "text-success"}>
                            {m.is_active ? <UserRoundX /> : <UserRoundCheck />}
                          </Button>
                        )}
                      </div>
                    </TableCell>
                  )}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}
      {editando !== undefined && <FormularioMembro key={editando?.id ?? "novo"} membro={editando} aberto aoFechar={() => setEditando(undefined)} />}
    </div>
  );
}
