import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQueryClient, useSuspenseQuery } from "@tanstack/react-query";
import { createFileRoute } from "@tanstack/react-router";
import { ImageIcon, LoaderCircle, X } from "lucide-react";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";

import { CabecalhoPagina } from "@/app/CabecalhoPagina";
import { LOGO_PADRAO } from "@/app/Marca";
import { PaginaCarregando } from "@/components/estado";
import { aplicarErrosApi, Campo, Secao } from "@/components/formulario";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { configQuery, type Configuracao } from "@/features/config/api";
import { api } from "@/lib/api";
import { aplicarMarca } from "@/lib/tema";

export const Route = createFileRoute("/_auth/administracao/configuracao")({
  loader: ({ context }) => context.queryClient.ensureQueryData(configQuery),
  pendingComponent: PaginaCarregando,
  component: PaginaConfiguracao,
});

const cor = z.string().regex(/^#[0-9a-fA-F]{6}$/, "Use o formato #RRGGBB");
const esquema = z.object({
  nome_organizacao: z.string().trim().min(2, "Informe o nome"),
  titulo_app: z.string().trim().min(2, "Informe o título"),
  sobre: z.string(),
  cor_primaria: cor,
  cor_secundaria: cor,
  email_contato: z.string().trim().email("E-mail inválido").or(z.literal("")),
  telefone_contato: z.string().trim(),
  site: z.string().trim().url("URL inválida").or(z.literal("")),
  instagram: z.string().trim(),
  endereco: z.string().trim(),
});
type Valores = z.infer<typeof esquema>;

type Imagem = "logo" | "favicon" | "banner";

function CampoImagem({ rotulo, atual, ajuda, aoEnviar, pendente }: { rotulo: string; atual: string | null; ajuda: string; aoEnviar: (f: File | null) => void; pendente: boolean }) {
  return (
    <Campo rotulo={rotulo} ajuda={ajuda}>
      <div className="flex items-center gap-3">
        <div className="flex size-16 shrink-0 items-center justify-center overflow-hidden rounded-lg border bg-white/90 p-1">
          {atual ? <img src={atual} alt="" className="size-full object-contain" /> : <ImageIcon className="size-6 text-muted-foreground" />}
        </div>
        <Input type="file" accept="image/*" className="max-w-xs" disabled={pendente} onChange={(e) => e.target.files?.[0] && aoEnviar(e.target.files[0])} />
        {atual && <Button type="button" variant="ghost" size="sm" disabled={pendente} onClick={() => aoEnviar(null)}><X /> Remover</Button>}
      </div>
    </Campo>
  );
}

function PaginaConfiguracao() {
  const queryClient = useQueryClient();
  const { data: cfg } = useSuspenseQuery(configQuery);
  const form = useForm<Valores>({
    resolver: zodResolver(esquema),
    defaultValues: {
      nome_organizacao: cfg.nome_organizacao, titulo_app: cfg.titulo_app, sobre: cfg.sobre,
      cor_primaria: cfg.cor_primaria, cor_secundaria: cfg.cor_secundaria, email_contato: cfg.email_contato,
      telefone_contato: cfg.telefone_contato, site: cfg.site, instagram: cfg.instagram, endereco: cfg.endereco,
    },
  });
  const erros = form.formState.errors;
  const r = form.register;
  const [enviando, setEnviando] = useState<Imagem | null>(null);

  function atualizado(nova: Configuracao) {
    queryClient.setQueryData(configQuery.queryKey, nova);
    aplicarMarca(nova);
  }
  const salvar = useMutation({
    mutationFn: (v: Valores) => api<Configuracao>("config/", { method: "PATCH", body: v }),
    onSuccess: (nova) => { atualizado(nova); toast.success("Identidade visual atualizada."); },
    onError: (erro) => aplicarErrosApi(form, erro),
  });
  const imagem = useMutation({
    mutationFn: ({ campo, arquivo }: { campo: Imagem; arquivo: File | null }) => {
      const fd = new FormData();
      fd.append(campo, arquivo ?? "");
      setEnviando(campo);
      return api<Configuracao>("config/", { method: "PATCH", body: fd });
    },
    onSuccess: (nova) => { atualizado(nova); toast.success("Imagem atualizada."); },
    onError: (e: Error) => toast.error(e.message),
    onSettled: () => setEnviando(null),
  });

  const primaria = form.watch("cor_primaria");
  const secundaria = form.watch("cor_secundaria");

  return (
    <div className="mx-auto max-w-3xl space-y-4">
      <CabecalhoPagina titulo="Identidade visual" descricao="Nome, cores e imagens que aparecem no CRM. O logo oficial da Atlética já vem embutido; suba outro só se mudar." />
      <form className="space-y-4" noValidate onSubmit={form.handleSubmit((v) => salvar.mutate(v))}>
        <Secao titulo="Organização">
          <Campo id="nome_organizacao" rotulo="Nome da organização" obrigatorio erro={erros.nome_organizacao?.message}><Input id="nome_organizacao" {...r("nome_organizacao")} /></Campo>
          <Campo id="titulo_app" rotulo="Título do aplicativo" obrigatorio erro={erros.titulo_app?.message} ajuda="Aparece na aba do navegador"><Input id="titulo_app" {...r("titulo_app")} /></Campo>
          <Campo id="sobre" rotulo="Sobre" erro={erros.sobre?.message} className="sm:col-span-2"><Textarea id="sobre" rows={3} {...r("sobre")} /></Campo>
        </Secao>

        <Secao titulo="Cores" descricao="Os tokens do tema seguem a paleta oficial; estas cores entram como acento de marca (logo, login).">
          <Campo id="cor_primaria" rotulo="Cor primária" erro={erros.cor_primaria?.message}>
            <div className="flex items-center gap-2">
              <input type="color" className="size-9 cursor-pointer rounded border bg-transparent p-0.5" value={primaria} onChange={(e) => form.setValue("cor_primaria", e.target.value, { shouldDirty: true })} aria-label="Escolher cor primária" />
              <Input id="cor_primaria" className="font-mono" {...r("cor_primaria")} aria-invalid={!!erros.cor_primaria} />
            </div>
          </Campo>
          <Campo id="cor_secundaria" rotulo="Cor secundária" erro={erros.cor_secundaria?.message}>
            <div className="flex items-center gap-2">
              <input type="color" className="size-9 cursor-pointer rounded border bg-transparent p-0.5" value={secundaria} onChange={(e) => form.setValue("cor_secundaria", e.target.value, { shouldDirty: true })} aria-label="Escolher cor secundária" />
              <Input id="cor_secundaria" className="font-mono" {...r("cor_secundaria")} aria-invalid={!!erros.cor_secundaria} />
            </div>
          </Campo>
          <div className="sm:col-span-2 flex items-center gap-3 rounded-lg border p-3">
            <div className="flex size-10 items-center justify-center rounded-lg" style={{ background: primaria }}><img src={cfg.logo || LOGO_PADRAO} alt="" className="size-7 object-contain" /></div>
            <div className="h-3 flex-1 rounded-full" style={{ background: `linear-gradient(90deg, ${primaria}, ${secundaria})` }} />
            <span className="text-xs text-muted-foreground">prévia</span>
          </div>
        </Secao>

        <Secao titulo="Contato">
          <Campo id="email_contato" rotulo="E-mail" erro={erros.email_contato?.message}><Input id="email_contato" type="email" {...r("email_contato")} /></Campo>
          <Campo id="telefone_contato" rotulo="Telefone" erro={erros.telefone_contato?.message}><Input id="telefone_contato" {...r("telefone_contato")} /></Campo>
          <Campo id="site" rotulo="Site" erro={erros.site?.message}><Input id="site" type="url" placeholder="https://…" {...r("site")} /></Campo>
          <Campo id="instagram" rotulo="Instagram" erro={erros.instagram?.message}><Input id="instagram" placeholder="@atletica" {...r("instagram")} /></Campo>
          <Campo id="endereco" rotulo="Endereço" erro={erros.endereco?.message} className="sm:col-span-2"><Input id="endereco" {...r("endereco")} /></Campo>
        </Secao>

        <div className="flex justify-end">
          <Button type="submit" disabled={salvar.isPending}>{salvar.isPending && <LoaderCircle className="animate-spin" />} Salvar</Button>
        </div>
      </form>

      <Secao titulo="Imagens" descricao="Salvas na hora, independente do botão acima. Em produção o disco é efêmero: suba de novo após um redeploy.">
        <CampoImagem rotulo="Logo" atual={cfg.logo} ajuda="PNG com fundo transparente, quadrado" pendente={enviando === "logo"} aoEnviar={(a) => imagem.mutate({ campo: "logo", arquivo: a })} />
        <CampoImagem rotulo="Favicon" atual={cfg.favicon} ajuda="Ícone da aba, 64×64" pendente={enviando === "favicon"} aoEnviar={(a) => imagem.mutate({ campo: "favicon", arquivo: a })} />
        <CampoImagem rotulo="Banner" atual={cfg.banner} ajuda="Imagem de capa (uso futuro)" pendente={enviando === "banner"} aoEnviar={(a) => imagem.mutate({ campo: "banner", arquivo: a })} />
      </Secao>
    </div>
  );
}
