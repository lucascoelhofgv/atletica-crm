import { useMutation, useQueryClient, useSuspenseQuery } from "@tanstack/react-query";
import { createFileRoute, Link, useRouter } from "@tanstack/react-router";
import { FileText, LoaderCircle, Mail, MapPin, MessageCircle, Pencil, Phone, Plus, Trash2, UserRound } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

import { CabecalhoPagina } from "@/app/CabecalhoPagina";
import { ConfirmarExclusao } from "@/components/ConfirmarExclusao";
import { PaginaCarregando, Vazio } from "@/components/estado";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Textarea } from "@/components/ui/textarea";
import { usePermissao } from "@/features/auth/queries";
import {
  avaliarFornecedor, chaves, enviarContrato, excluirAvaliacao, excluirFornecedor, fornecedorQuery,
} from "@/features/fornecedores/api";
import { Estrelas } from "@/features/fornecedores/components/Estrelas";
import type { AvaliacaoEntrada, Fornecedor } from "@/features/fornecedores/types";
import { data as fmtData, moeda, numero, relativo } from "@/lib/formatos";

export const Route = createFileRoute("/_auth/fornecedores/$id/")({
  loader: ({ context, params }) => context.queryClient.ensureQueryData(fornecedorQuery(Number(params.id))),
  pendingComponent: PaginaCarregando,
  component: PaginaFornecedor,
});

const CRITERIOS: { chave: keyof Omit<AvaliacaoEntrada, "comentario">; rotulo: string }[] = [
  { chave: "preco", rotulo: "Preço" },
  { chave: "qualidade", rotulo: "Qualidade" },
  { chave: "prazo", rotulo: "Prazo" },
  { chave: "atendimento", rotulo: "Atendimento" },
  { chave: "confiabilidade", rotulo: "Confiabilidade" },
];

function NovaAvaliacao({ fornecedor, aoAtualizar }: { fornecedor: Fornecedor; aoAtualizar: (f: Fornecedor) => void }) {
  const [aberto, setAberto] = useState(false);
  const [notas, setNotas] = useState<AvaliacaoEntrada>({ preco: 3, qualidade: 3, prazo: 3, atendimento: 3, confiabilidade: 3, comentario: "" });
  const avaliar = useMutation({
    mutationFn: () => avaliarFornecedor(fornecedor.id, notas),
    onSuccess: (f) => { aoAtualizar(f); toast.success("Avaliação registrada."); setAberto(false); },
    onError: (erro: Error) => toast.error(erro.message),
  });
  const media = CRITERIOS.reduce((s, c) => s + notas[c.chave], 0) / CRITERIOS.length;
  return (
    <Dialog open={aberto} onOpenChange={setAberto}>
      <DialogTrigger asChild><Button size="sm" variant="outline"><Plus /> Avaliar</Button></DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Avaliar {fornecedor.nome_exibicao}</DialogTitle>
          <DialogDescription>Notas de 1 a 5 em cada critério. Média: {media.toFixed(1)}.</DialogDescription>
        </DialogHeader>
        <div className="space-y-3">
          {CRITERIOS.map((c) => (
            <div key={c.chave} className="flex items-center justify-between">
              <span className="text-sm">{c.rotulo}</span>
              <Estrelas valor={notas[c.chave]} aoMudar={(v) => setNotas((n) => ({ ...n, [c.chave]: v }))} tamanho="size-5" />
            </div>
          ))}
          <Textarea rows={2} placeholder="Comentário (opcional)" value={notas.comentario} onChange={(e) => setNotas((n) => ({ ...n, comentario: e.target.value }))} />
          <div className="flex justify-end gap-2">
            <Button type="button" variant="ghost" onClick={() => setAberto(false)}>Cancelar</Button>
            <Button onClick={() => avaliar.mutate()} disabled={avaliar.isPending}>{avaliar.isPending && <LoaderCircle className="animate-spin" />} Salvar avaliação</Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}

function Linha({ icone: Icone, valor, href }: { icone: typeof Mail; valor: string; href?: string }) {
  if (!valor) return null;
  const c = <span className="flex items-center gap-2 text-sm"><Icone className="size-4 shrink-0 text-muted-foreground" /> {valor}</span>;
  return href ? <a href={href} target="_blank" rel="noreferrer" className="hover:underline">{c}</a> : c;
}

function Bloco({ rotulo, valor }: { rotulo: string; valor?: string }) {
  if (!valor) return null;
  return (
    <div>
      <div className="text-[11px] uppercase tracking-wide text-muted-foreground">{rotulo}</div>
      <p className="whitespace-pre-line text-sm">{valor}</p>
    </div>
  );
}

function PaginaFornecedor() {
  const { id } = Route.useParams();
  const router = useRouter();
  const queryClient = useQueryClient();
  const permissao = usePermissao("fornecedores");
  const { data: f } = useSuspenseQuery(fornecedorQuery(Number(id)));

  function atualizar(novo: Fornecedor) {
    queryClient.setQueryData(chaves.detalhe(novo.id), novo);
    void queryClient.invalidateQueries({ queryKey: chaves.todos });
  }
  const excluir = useMutation({
    mutationFn: () => excluirFornecedor(f.id),
    onSuccess: () => { void queryClient.invalidateQueries({ queryKey: chaves.todos }); toast.success("Fornecedor excluído."); void router.navigate({ to: "/fornecedores" }); },
    onError: (erro: Error) => toast.error(erro.message),
  });
  const apagarAvaliacao = useMutation({ mutationFn: (aid: number) => excluirAvaliacao(f.id, aid), onSuccess: atualizar, onError: (e: Error) => toast.error(e.message) });
  const contrato = useMutation({ mutationFn: (a: File | null) => enviarContrato(f.id, a), onSuccess: (n) => { atualizar(n); toast.success("Contrato atualizado."); }, onError: (e: Error) => toast.error(e.message) });
  const whats = f.whatsapp.replace(/\D/g, "");

  return (
    <div className="space-y-6">
      <CabecalhoPagina
        titulo={f.nome_exibicao}
        voltar={{ para: "/fornecedores", rotulo: "Fornecedores" }}
        descricao={
          <span className="flex flex-wrap items-center gap-1.5">
            <Badge variant="secondary" className="font-normal">{f.categoria_rotulo}</Badge>
            <Badge variant={f.status === "ativo" ? "secondary" : "outline"} className="font-normal">{f.status_rotulo}</Badge>
            {f.nome_fantasia && <span className="text-xs text-muted-foreground">{f.nome}</span>}
            {f.nota_media !== null && <span className="flex items-center gap-1 text-xs text-muted-foreground"><Estrelas valor={f.nota_media} tamanho="size-3.5" /> {f.nota_media.toFixed(1)}</span>}
          </span>
        }
        acoes={
          permissao.escrever ? (
            <>
              <NovaAvaliacao fornecedor={f} aoAtualizar={atualizar} />
              <Button asChild size="sm" variant="outline"><Link to="/fornecedores/$id/editar" params={{ id }}><Pencil /> Editar</Link></Button>
              {permissao.excluir && (
                <ConfirmarExclusao titulo={`Excluir ${f.nome_exibicao}?`} descricao="Os produtos ligados a ele ficam sem fornecedor. As avaliações somem." aoConfirmar={() => excluir.mutateAsync()} pendente={excluir.isPending} />
              )}
            </>
          ) : undefined
        }
      />

      <div className="grid gap-4 lg:grid-cols-3">
        <Card>
          <CardHeader><CardTitle>Contato</CardTitle></CardHeader>
          <CardContent className="space-y-2">
            <Linha icone={UserRound} valor={f.contato_nome} />
            <Linha icone={Mail} valor={f.email} href={f.email ? `mailto:${f.email}` : undefined} />
            <Linha icone={MessageCircle} valor={f.whatsapp} href={whats ? `https://wa.me/55${whats}` : undefined} />
            <Linha icone={Phone} valor={f.telefone} />
            <Linha icone={MapPin} valor={f.endereco} />
            {f.documento && <div className="pt-1 text-xs text-muted-foreground">Documento: {f.documento}</div>}
            <div className="flex items-center gap-2 border-t pt-3 text-xs">
              <FileText className="size-3.5 text-muted-foreground" />
              {f.contrato ? <a href={f.contrato} target="_blank" rel="noreferrer" className="hover:underline">ver contrato</a> : <span className="text-muted-foreground">sem contrato anexado</span>}
              {permissao.escrever && (
                <label className="ml-auto cursor-pointer text-muted-foreground hover:text-foreground">
                  {contrato.isPending ? "enviando…" : f.contrato ? "trocar" : "anexar"}
                  <input type="file" className="hidden" accept=".pdf,image/*,.doc,.docx" onChange={(e) => e.target.files?.[0] && contrato.mutate(e.target.files[0])} />
                </label>
              )}
            </div>
          </CardContent>
        </Card>

        <Card className="lg:col-span-2">
          <CardHeader><CardTitle>Comercial</CardTitle></CardHeader>
          <CardContent className="grid gap-4 sm:grid-cols-2">
            <Bloco rotulo="Produtos ou serviços" valor={f.produtos_servicos} />
            <Bloco rotulo="Condições comerciais" valor={f.condicoes_comerciais} />
            <Bloco rotulo="Prazo médio de entrega" valor={f.prazo_medio_entrega} />
            <Bloco rotulo="Observações" valor={f.observacoes} />
            {!f.produtos_servicos && !f.condicoes_comerciais && !f.prazo_medio_entrega && !f.observacoes && (
              <p className="text-sm text-muted-foreground sm:col-span-2">Nada registrado ainda.</p>
            )}
            <div className="text-xs text-muted-foreground sm:col-span-2">Cadastrado em {fmtData(f.criado_em)}{f.criado_por && ` por ${f.criado_por.nome}`}</div>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Produtos fornecidos</CardTitle>
            <CardDescription>{numero(f.qtd_produtos)} no catálogo</CardDescription>
          </CardHeader>
          <CardContent>
            {f.produtos.length === 0 ? (
              <Vazio titulo="Nenhum produto ligado" className="py-8" />
            ) : (
              <ul className="divide-y">
                {f.produtos.map((p) => (
                  <li key={p.id} className="flex items-center justify-between py-2 text-sm">
                    <Link to="/produtos/$id" params={{ id: String(p.id) }} className="hover:underline">{p.nome}</Link>
                    <span className="tabular text-xs text-muted-foreground">{numero(p.quantidade_atual)} un. · {moeda(p.preco_venda)}</span>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Avaliações</CardTitle>
            <CardDescription>{f.qtd_avaliacoes === 0 ? "Ninguém avaliou ainda" : `Média ${f.nota_media?.toFixed(1)} em ${numero(f.qtd_avaliacoes)} ${f.qtd_avaliacoes === 1 ? "avaliação" : "avaliações"}`}</CardDescription>
          </CardHeader>
          <CardContent>
            {f.avaliacoes.length === 0 ? (
              <Vazio titulo="Sem avaliações" descricao="Avalie depois de uma compra para a equipe saber com quem vale a pena trabalhar." className="py-8" />
            ) : (
              <ul className="space-y-3">
                {f.avaliacoes.map((a) => (
                  <li key={a.id} className="group rounded-lg border p-3">
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex items-center gap-2"><Estrelas valor={a.media} /><span className="tabular text-sm font-medium">{a.media.toFixed(1)}</span></div>
                      {permissao.escrever && (
                        <button type="button" onClick={() => apagarAvaliacao.mutate(a.id)} className="text-muted-foreground opacity-0 hover:text-destructive group-hover:opacity-100 pointer-coarse:opacity-100" aria-label="Excluir avaliação"><Trash2 className="size-3.5" /></button>
                      )}
                    </div>
                    <div className="mt-1 grid grid-cols-5 gap-1 text-[11px] text-muted-foreground">
                      {CRITERIOS.map((c) => <span key={c.chave}>{c.rotulo.slice(0, 5)}. <span className="tabular text-foreground">{a[c.chave]}</span></span>)}
                    </div>
                    {a.comentario && <p className="mt-1 text-sm">{a.comentario}</p>}
                    <div className="mt-1 text-[11px] text-muted-foreground">{a.autor?.nome ?? "—"} · {relativo(a.criado_em)}</div>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
