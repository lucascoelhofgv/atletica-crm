import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { createFileRoute } from "@tanstack/react-router";
import { AlertTriangle, CheckCircle2, ExternalLink, Eye, LoaderCircle, Plus, RefreshCw, XCircle } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

import { CabecalhoPagina } from "@/app/CabecalhoPagina";
import { ConfirmarExclusao } from "@/components/ConfirmarExclusao";
import { ErroCarregamento, PaginaCarregando, Vazio } from "@/components/estado";
import { Campo, Secao } from "@/components/formulario";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { fontesQuery, opcoesFontesQuery, sincronizarFonte } from "@/features/esportes/api";
import type { FontePlanilha } from "@/features/esportes/types";
import { api } from "@/lib/api";
import { dataHora, relativo } from "@/lib/formatos";

export const Route = createFileRoute("/_auth/administracao/fontes")({
  component: PaginaFontes,
});

/** Destinos que leem uma tabela simples e por isso aceitam "modo". */
const COM_MODO = new Set(["clientes", "fornecedores"]);

interface Execucao {
  simulacao: boolean;
  resumo: string;
  avisos: string[];
}

function NovaFonte({ aoCriar }: { aoCriar: () => void }) {
  const { data: opcoes } = useQuery(opcoesFontesQuery);
  const [nome, setNome] = useState("");
  const [planilha, setPlanilha] = useState("");
  const [aba, setAba] = useState("");
  const [destino, setDestino] = useState("esportes_treinos");
  const [modo, setModo] = useState("criar_atualizar");

  const criar = useMutation({
    mutationFn: () =>
      api<FontePlanilha>("integracoes/fontes/", {
        method: "POST",
        body: { nome: nome.trim(), planilha: planilha.trim(), aba: aba.trim(), destino, modo },
      }),
    onSuccess: (f) => {
      toast.success(`"${f.nome}" cadastrada. Clique em Simular para conferir a leitura.`);
      setNome("");
      setPlanilha("");
      setAba("");
      aoCriar();
    },
    onError: (e: Error) => toast.error(e.message),
  });

  return (
    <Secao
      titulo="Cadastrar planilha"
      descricao={
        opcoes?.conta_servico ? (
          <>
            Antes, compartilhe a planilha (leitor basta) com <span className="font-medium text-foreground">{opcoes.conta_servico}</span>.
            Vale Planilha Google e arquivo .xlsx guardado no Drive.
          </>
        ) : (
          "A credencial do Google não está configurada neste servidor (ver docs/DEPLOY.md)."
        )
      }
    >
      <Campo id="nome" rotulo="Nome" obrigatorio>
        <Input id="nome" value={nome} onChange={(e) => setNome(e.target.value)} placeholder="Treinos 26.1" />
      </Campo>
      <Campo id="destino" rotulo="Importar como">
        <Select value={destino} onValueChange={setDestino}>
          <SelectTrigger id="destino" className="w-full">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {opcoes?.destinos.map((o) => (
              <SelectItem key={o.valor} value={o.valor}>
                {o.rotulo}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </Campo>
      <Campo id="planilha" rotulo="URL da planilha" obrigatorio className="sm:col-span-2">
        <Input id="planilha" value={planilha} onChange={(e) => setPlanilha(e.target.value)} placeholder="https://docs.google.com/spreadsheets/d/…" />
      </Campo>
      <Campo id="aba" rotulo="Aba" ajuda={destino === "esportes_treinos" ? "Em branco lê todas as abas visíveis" : "Em branco usa a primeira"}>
        <Input id="aba" value={aba} onChange={(e) => setAba(e.target.value)} />
      </Campo>
      {COM_MODO.has(destino) && (
        <Campo id="modo" rotulo="Modo">
          <Select value={modo} onValueChange={setModo}>
            <SelectTrigger id="modo" className="w-full">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {opcoes?.modos.map((o) => (
                <SelectItem key={o.valor} value={o.valor}>
                  {o.rotulo}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </Campo>
      )}
      <div className="sm:col-span-2">
        <Button onClick={() => criar.mutate()} disabled={!nome.trim() || !planilha.trim() || criar.isPending}>
          {criar.isPending ? <LoaderCircle className="animate-spin" /> : <Plus />} Cadastrar
        </Button>
      </div>
    </Secao>
  );
}

function CartaoFonte({ fonte }: { fonte: FontePlanilha }) {
  const queryClient = useQueryClient();
  const [execucao, setExecucao] = useState<Execucao | null>(null);
  const atualizar = () => {
    void queryClient.invalidateQueries({ queryKey: ["integracoes", "fontes"] });
    void queryClient.invalidateQueries({ queryKey: ["esportes"] });
  };

  const rodar = useMutation({
    mutationFn: (simular: boolean) => sincronizarFonte(fonte.id, simular).then((r) => ({ ...r, simulacao: simular })),
    onSuccess: (r) => {
      setExecucao({ simulacao: r.simulacao, resumo: r.resumo, avisos: r.avisos });
      toast.success(r.simulacao ? `Simulação: ${r.resumo}` : `${fonte.nome}: ${r.resumo}`);
    },
    onError: (e: Error) => {
      setExecucao(null);
      toast.error(e.message);
    },
    onSettled: atualizar,
  });
  const alternar = useMutation({
    mutationFn: (ativa: boolean) => api(`integracoes/fontes/${fonte.id}/`, { method: "PATCH", body: { ativa } }),
    onSuccess: atualizar,
    onError: (e: Error) => toast.error(e.message),
  });
  const excluir = useMutation({
    mutationFn: () => api(`integracoes/fontes/${fonte.id}/`, { method: "DELETE" }),
    onSuccess: () => {
      toast.success(`"${fonte.nome}" removida. Os dados já importados continuam no CRM.`);
      atualizar();
    },
    onError: (e: Error) => toast.error(e.message),
  });

  return (
    <Card>
      <CardHeader className="gap-2">
        <div className="flex flex-wrap items-start justify-between gap-2">
          <div className="min-w-0">
            <CardTitle>{fonte.nome}</CardTitle>
            <CardDescription>
              <a href={fonte.planilha} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 hover:underline">
                Abrir planilha <ExternalLink className="size-3" />
              </a>
              {fonte.aba && <> · aba {fonte.aba}</>}
            </CardDescription>
          </div>
          <Badge variant="secondary" className="font-normal">
            {fonte.destino_rotulo}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="text-sm">
          {fonte.ultimo_erro ? (
            <p className="flex items-start gap-1.5 text-destructive">
              <XCircle className="mt-0.5 size-4 shrink-0" /> Falhou na última tentativa: {fonte.ultimo_erro}
            </p>
          ) : fonte.ultima_sincronizacao ? (
            <p className="flex items-start gap-1.5">
              <CheckCircle2 className="mt-0.5 size-4 shrink-0 text-success" />
              <span>
                <span title={dataHora(fonte.ultima_sincronizacao)}>Sincronizada {relativo(fonte.ultima_sincronizacao)}</span>
                <span className="text-muted-foreground">: {fonte.ultimo_resultado}</span>
              </span>
            </p>
          ) : (
            <p className="text-muted-foreground">Ainda não sincronizada.</p>
          )}
        </div>

        {execucao && execucao.avisos.length > 0 && (
          <div className="rounded-lg border border-warning/40 bg-warning/5 p-3 text-xs">
            <div className="mb-1 flex items-center gap-1.5 font-medium">
              <AlertTriangle className="size-3.5 text-warning" />
              {execucao.avisos.length} linha(s) para conferir na planilha
              {execucao.simulacao && <span className="font-normal text-muted-foreground">(simulação, nada foi gravado)</span>}
            </div>
            <ul className="list-disc space-y-0.5 pl-5 text-muted-foreground">
              {execucao.avisos.map((a, i) => (
                <li key={i}>{a}</li>
              ))}
            </ul>
          </div>
        )}

        <div className="flex flex-wrap items-center gap-2">
          <Button size="sm" onClick={() => rodar.mutate(false)} disabled={rodar.isPending}>
            {rodar.isPending && !rodar.variables ? <LoaderCircle className="animate-spin" /> : <RefreshCw />} Sincronizar agora
          </Button>
          <Button size="sm" variant="outline" onClick={() => rodar.mutate(true)} disabled={rodar.isPending}>
            {rodar.isPending && rodar.variables ? <LoaderCircle className="animate-spin" /> : <Eye />} Simular
          </Button>
          <label className="flex items-center gap-2 text-xs text-muted-foreground sm:ml-auto">
            <Switch checked={fonte.ativa} onCheckedChange={(v) => alternar.mutate(v)} disabled={alternar.isPending} />
            Entra na sincronização automática
          </label>
          <ConfirmarExclusao
            titulo={`Remover "${fonte.nome}"?`}
            descricao="O CRM para de ler esta planilha. O que já foi importado continua aqui."
            aoConfirmar={() => excluir.mutateAsync()}
            pendente={excluir.isPending}
            rotuloBotao="Remover"
            variante="ghost"
          />
        </div>
      </CardContent>
    </Card>
  );
}

function PaginaFontes() {
  const queryClient = useQueryClient();
  const consulta = useQuery(fontesQuery);

  if (consulta.isError && !consulta.data) return <ErroCarregamento erro={consulta.error} tentarDeNovo={() => consulta.refetch()} />;
  if (!consulta.data) return <PaginaCarregando />;

  return (
    <div className="mx-auto max-w-4xl space-y-4">
      <CabecalhoPagina
        titulo="Fontes de planilha"
        descricao="As planilhas que alimentam o CRM. A planilha continua sendo onde a diretoria edita; aqui o CRM só lê."
      />
      <NovaFonte aoCriar={() => void queryClient.invalidateQueries({ queryKey: ["integracoes", "fontes"] })} />
      {consulta.data.length === 0 ? (
        <Vazio titulo="Nenhuma planilha cadastrada" descricao="Cadastre a primeira acima." />
      ) : (
        consulta.data.map((f) => <CartaoFonte key={f.id} fonte={f} />)
      )}
    </div>
  );
}
