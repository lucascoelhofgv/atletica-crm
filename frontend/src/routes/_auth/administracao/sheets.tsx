import { useMutation, useQuery } from "@tanstack/react-query";
import { createFileRoute, Link } from "@tanstack/react-router";
import { CheckCircle2, ExternalLink, FileSpreadsheet, Import, LoaderCircle, PartyPopper, XCircle } from "lucide-react";
import { toast } from "sonner";

import { CabecalhoPagina } from "@/app/CabecalhoPagina";
import { ErroCarregamento, PaginaCarregando } from "@/components/estado";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { api } from "@/lib/api";

export const Route = createFileRoute("/_auth/administracao/sheets")({
  component: PaginaSheets,
});

interface Situacao {
  configurado: boolean;
  planilha_id: string;
  url_planilha: string;
  abas_exportadas: string[];
  destinos: { valor: string; rotulo: string }[];
  sugeridas: { rotulo: string; planilha: string; destino: string }[];
}

function PaginaSheets() {
  const consulta = useQuery({ queryKey: ["integracoes", "sheets"], queryFn: () => api<Situacao>("integracoes/sheets/") });
  const d = consulta.data;
  const exportar = useMutation({
    mutationFn: () => api<{ resumo: Record<string, number> }>("integracoes/sheets/exportar/", { method: "POST", timeoutMs: 90_000 }),
    onSuccess: ({ resumo }) => toast.success(`Planilha atualizada: ${Object.entries(resumo).map(([k, v]) => `${k} ${v}`).join(", ")}.`),
    onError: (e: Error) => toast.error(e.message),
  });
  const festas = useMutation({
    mutationFn: () => api<{ eventos: number }>("integracoes/sheets/festas/", { method: "POST", timeoutMs: 90_000 }),
    onSuccess: ({ eventos }) => toast.success(`Aba "Festas" atualizada com ${eventos} evento(s).`),
    onError: (e: Error) => toast.error(e.message),
  });

  if (consulta.isError && !d) return <ErroCarregamento erro={consulta.error} tentarDeNovo={() => consulta.refetch()} />;
  if (!d) return <PaginaCarregando />;

  return (
    <div className="mx-auto max-w-3xl space-y-4">
      <CabecalhoPagina
        titulo="Google Sheets"
        descricao="Exporta os dados do CRM para a planilha configurada, para análises fora do sistema."
        acoes={<Button asChild variant="outline" size="sm"><Link to="/administracao/importar" search={{}}><Import /> Importar de planilha</Link></Button>}
      />
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            {d.configurado ? <CheckCircle2 className="size-5 text-success" /> : <XCircle className="size-5 text-destructive" />}
            {d.configurado ? "Integração configurada" : "Integração não configurada"}
          </CardTitle>
          <CardDescription>
            {d.configurado ? (
              <a href={d.url_planilha} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 hover:underline">abrir a planilha de destino <ExternalLink className="size-3.5" /></a>
            ) : (
              "Defina GOOGLE_SHEETS_SPREADSHEET_ID e as credenciais da service account no ambiente (ver docs/DEPLOY.md)."
            )}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-wrap gap-1">
            {d.abas_exportadas.map((a) => <Badge key={a} variant="secondary" className="font-normal">{a}</Badge>)}
          </div>
          <div className="flex flex-wrap gap-2">
            <Button onClick={() => exportar.mutate()} disabled={!d.configurado || exportar.isPending}>
              {exportar.isPending ? <LoaderCircle className="animate-spin" /> : <FileSpreadsheet />} Sincronizar dados gerais
            </Button>
            <Button variant="outline" onClick={() => festas.mutate()} disabled={!d.configurado || festas.isPending}>
              {festas.isPending ? <LoaderCircle className="animate-spin" /> : <PartyPopper />} Sincronizar aba Festas
            </Button>
          </div>
          <p className="text-xs text-muted-foreground">A sincronização sobrescreve as abas com o estado atual do CRM. Pode levar alguns segundos.</p>
        </CardContent>
      </Card>
    </div>
  );
}
