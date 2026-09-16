import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { createFileRoute } from "@tanstack/react-router";
import { Eye, LoaderCircle, Upload } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";
import { z } from "zod";

import { CabecalhoPagina } from "@/app/CabecalhoPagina";
import { Campo, Secao } from "@/components/formulario";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { api } from "@/lib/api";
import { numero } from "@/lib/formatos";

const buscaSchema = z.object({
  planilha: z.string().optional().catch(undefined),
  destino: z.string().optional().catch(undefined),
});

export const Route = createFileRoute("/_auth/administracao/importar")({
  validateSearch: buscaSchema,
  component: PaginaImportar,
});

interface Situacao {
  destinos: { valor: string; rotulo: string }[];
  sugeridas: { rotulo: string; planilha: string; destino: string }[];
}
interface Previa { destino_rotulo: string; cabecalho: string[]; amostra: string[][]; total_linhas: number }
interface Resultado { destino_rotulo: string; criados: number; atualizados: number; ignorados: number; erros: string[] }

function PaginaImportar() {
  const busca = Route.useSearch();
  const queryClient = useQueryClient();
  const { data: sit } = useQuery({ queryKey: ["integracoes", "sheets"], queryFn: () => api<Situacao>("integracoes/sheets/") });
  const [planilha, setPlanilha] = useState(busca.planilha ?? "");
  const [aba, setAba] = useState("");
  const [destino, setDestino] = useState(busca.destino ?? "clientes");
  const [modo, setModo] = useState("criar_atualizar");
  const [previa, setPrevia] = useState<Previa | null>(null);
  const [resultado, setResultado] = useState<Resultado | null>(null);

  const corpo = { planilha: planilha.trim(), aba: aba.trim(), destino, modo };
  const verPrevia = useMutation({
    mutationFn: () => api<Previa>("integracoes/importar/previa/", { method: "POST", body: corpo, timeoutMs: 90_000 }),
    onSuccess: (p) => { setPrevia(p); setResultado(null); },
    onError: (e: Error) => toast.error(e.message),
  });
  const importar = useMutation({
    mutationFn: () => api<Resultado>("integracoes/importar/", { method: "POST", body: corpo, timeoutMs: 120_000 }),
    onSuccess: (r) => {
      setResultado(r);
      void queryClient.invalidateQueries({ queryKey: ["clientes"] });
      void queryClient.invalidateQueries({ queryKey: ["fornecedores"] });
      void queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      toast.success(`${r.destino_rotulo}: ${r.criados} criado(s), ${r.atualizados} atualizado(s).`);
    },
    onError: (e: Error) => toast.error(e.message),
  });

  return (
    <div className="mx-auto max-w-4xl space-y-4">
      <CabecalhoPagina titulo="Importar de planilha" descricao="Lê uma aba do Google Sheets e cria (ou completa) clientes e fornecedores. Veja a prévia antes de gravar." />

      {sit && sit.sugeridas.length > 0 && (
        <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
          Planilhas conhecidas:
          {sit.sugeridas.map((s) => (
            <Button key={s.planilha} variant="outline" size="sm" className="h-7 text-xs" onClick={() => { setPlanilha(s.planilha); setDestino(s.destino); setPrevia(null); setResultado(null); }}>{s.rotulo}</Button>
          ))}
        </div>
      )}

      <Secao titulo="Origem" descricao="A planilha precisa estar compartilhada com a service account (ver docs/DEPLOY.md).">
        <Campo id="planilha" rotulo="URL ou ID da planilha" obrigatorio className="sm:col-span-2"><Input id="planilha" value={planilha} onChange={(e) => setPlanilha(e.target.value)} placeholder="https://docs.google.com/spreadsheets/d/…" /></Campo>
        <Campo id="aba" rotulo="Nome da aba" ajuda="Em branco usa a primeira"><Input id="aba" value={aba} onChange={(e) => setAba(e.target.value)} /></Campo>
        <Campo id="destino" rotulo="Importar como">
          <Select value={destino} onValueChange={(v) => { setDestino(v); setPrevia(null); }}><SelectTrigger id="destino" className="w-full"><SelectValue /></SelectTrigger><SelectContent>{sit?.destinos.map((o) => <SelectItem key={o.valor} value={o.valor}>{o.rotulo}</SelectItem>)}</SelectContent></Select>
        </Campo>
        <Campo id="modo" rotulo="Modo" className="sm:col-span-2">
          <Select value={modo} onValueChange={setModo}><SelectTrigger id="modo" className="w-full"><SelectValue /></SelectTrigger><SelectContent>
            <SelectItem value="criar_atualizar">Criar novos e completar dados dos existentes</SelectItem>
            <SelectItem value="somente_criar">Só criar novos (ignorar quem já existe)</SelectItem>
          </SelectContent></Select>
        </Campo>
        <div className="flex gap-2 sm:col-span-2">
          <Button variant="outline" onClick={() => verPrevia.mutate()} disabled={!planilha.trim() || verPrevia.isPending}>{verPrevia.isPending ? <LoaderCircle className="animate-spin" /> : <Eye />} Ver prévia</Button>
          <Button onClick={() => importar.mutate()} disabled={!previa || importar.isPending}>{importar.isPending ? <LoaderCircle className="animate-spin" /> : <Upload />} Importar {previa ? `${numero(previa.total_linhas)} linhas` : ""}</Button>
        </div>
      </Secao>

      {previa && (
        <Card>
          <CardHeader>
            <CardTitle>Prévia · {previa.destino_rotulo}</CardTitle>
            <CardDescription>{numero(previa.total_linhas)} linhas lidas · mostrando as primeiras {previa.amostra.length} · colunas detectadas: {previa.cabecalho.join(", ")}</CardDescription>
          </CardHeader>
          <CardContent className="overflow-x-auto">
            <Table>
              <TableHeader><TableRow>{previa.cabecalho.map((c) => <TableHead key={c}>{c}</TableHead>)}</TableRow></TableHeader>
              <TableBody>{previa.amostra.map((linha, i) => <TableRow key={i}>{linha.map((v, j) => <TableCell key={j} className="max-w-48 truncate">{v || <span className="text-muted-foreground">—</span>}</TableCell>)}</TableRow>)}</TableBody>
            </Table>
          </CardContent>
        </Card>
      )}

      {resultado && (
        <Card>
          <CardHeader><CardTitle>Resultado</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            <div className="flex flex-wrap gap-2">
              <Badge variant="secondary" className="bg-success/15 font-normal text-success">{numero(resultado.criados)} criados</Badge>
              <Badge variant="secondary" className="font-normal">{numero(resultado.atualizados)} atualizados</Badge>
              <Badge variant="outline" className="font-normal">{numero(resultado.ignorados)} ignorados</Badge>
              {resultado.erros.length > 0 && <Badge variant="secondary" className="bg-destructive/10 font-normal text-destructive">{numero(resultado.erros.length)} erros</Badge>}
            </div>
            {resultado.erros.length > 0 && <ul className="list-disc space-y-0.5 pl-5 text-xs text-muted-foreground">{resultado.erros.map((e, i) => <li key={i}>{e}</li>)}</ul>}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
