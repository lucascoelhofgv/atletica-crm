/**
 * Cliente HTTP da API do Django (mesma origem).
 *
 * - Sessão por cookie (`credentials: "same-origin"`).
 * - CSRF: lê o cookie `csrftoken` a cada requisição não segura e manda em
 *   `X-CSRFToken` (o Django rotaciona o token no login, então nunca cacheamos).
 * - Erros chegam como `ApiErro` com `codigo`, `mensagem` e `campos` (validação).
 * - 401 no meio da navegação: chama o callback registrado (volta pro login).
 */

export type Campos = Record<string, string[]>;

export class ApiErro extends Error {
  constructor(
    public status: number,
    public codigo: string,
    mensagem: string,
    public campos: Campos = {},
  ) {
    super(mensagem);
    this.name = "ApiErro";
  }

  get naoAutenticado() {
    return this.status === 401;
  }

  get validacao() {
    return this.status === 400;
  }
}

type Metodo = "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
type Params = Record<string, string | number | boolean | null | undefined>;

export interface OpcoesApi {
  method?: Metodo;
  body?: unknown;
  params?: Params;
  /** Milissegundos até abortar (padrão 20 s; Sheets usa 60 s). */
  timeoutMs?: number;
  /** Não dispara o callback global de 401 (usado pelo bootstrap do login). */
  silenciar401?: boolean;
  signal?: AbortSignal;
}

const METODOS_SEGUROS = new Set(["GET", "HEAD", "OPTIONS"]);

let aoNaoAutenticado: (() => void) | null = null;

/** Registrado uma vez em `main.tsx`: limpa o cache e manda para o login. */
export function definirAoNaoAutenticado(fn: () => void) {
  aoNaoAutenticado = fn;
}

export function lerCookie(nome: string): string | undefined {
  const prefixo = `${nome}=`;
  for (const parte of document.cookie.split("; ")) {
    if (parte.startsWith(prefixo)) return decodeURIComponent(parte.slice(prefixo.length));
  }
  return undefined;
}

export function montarUrl(caminho: string, params?: Params): string {
  const url = caminho.startsWith("/api/") ? caminho : `/api/${caminho.replace(/^\/+/, "")}`;
  if (!params) return url;
  const query = new URLSearchParams();
  for (const [chave, valor] of Object.entries(params)) {
    if (valor === undefined || valor === null || valor === "") continue;
    query.set(chave, String(valor));
  }
  const texto = query.toString();
  return texto ? `${url}?${texto}` : url;
}

export async function api<T = unknown>(caminho: string, opcoes: OpcoesApi = {}): Promise<T> {
  const method = opcoes.method ?? "GET";
  const headers = new Headers({ Accept: "application/json" });
  let body: BodyInit | undefined;

  if (opcoes.body instanceof FormData) {
    body = opcoes.body;
  } else if (opcoes.body !== undefined) {
    headers.set("Content-Type", "application/json");
    body = JSON.stringify(opcoes.body);
  }
  if (!METODOS_SEGUROS.has(method)) {
    headers.set("X-CSRFToken", lerCookie("csrftoken") ?? "");
  }

  const controlador = new AbortController();
  const timer = window.setTimeout(() => controlador.abort(), opcoes.timeoutMs ?? 20_000);
  opcoes.signal?.addEventListener("abort", () => controlador.abort(), { once: true });

  let resposta: Response;
  try {
    resposta = await fetch(montarUrl(caminho, opcoes.params), {
      method,
      headers,
      body,
      credentials: "same-origin",
      signal: controlador.signal,
    });
  } catch (erro) {
    window.clearTimeout(timer);
    if ((erro as Error).name === "AbortError") {
      throw new ApiErro(0, "tempo_esgotado", "O servidor demorou demais para responder.");
    }
    throw new ApiErro(0, "rede", "Sem conexão com o servidor. Verifique sua internet.");
  }
  window.clearTimeout(timer);

  if (resposta.status === 204) return undefined as T;

  const tipo = resposta.headers.get("content-type") ?? "";
  const dados = tipo.includes("json") ? await resposta.json().catch(() => null) : null;

  if (!resposta.ok) {
    const erro = (dados as { erro?: { codigo?: string; mensagem?: string; campos?: Campos } } | null)?.erro;
    const excecao = new ApiErro(
      resposta.status,
      erro?.codigo ?? (resposta.status === 401 ? "nao_autenticado" : "erro"),
      erro?.mensagem ?? mensagemPadrao(resposta.status),
      erro?.campos ?? {},
    );
    if (resposta.status === 401 && !opcoes.silenciar401) aoNaoAutenticado?.();
    throw excecao;
  }
  return dados as T;
}

function mensagemPadrao(status: number) {
  if (status === 401) return "Sua sessão expirou. Faça login de novo.";
  if (status === 403) return "Você não tem permissão para esta ação.";
  if (status === 404) return "Registro não encontrado.";
  if (status >= 500) return "Erro no servidor. Tente de novo em instantes.";
  return `Erro ${status}.`;
}

/** Resposta paginada padrão da API (apps/api/pagination.py). */
export interface Paginado<T> {
  total: number;
  pagina: number;
  paginas: number;
  resultados: T[];
}
