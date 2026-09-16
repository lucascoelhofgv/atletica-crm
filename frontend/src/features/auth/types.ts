export type Modulo =
  | "crm"
  | "catalogo"
  | "vendas"
  | "fornecedores"
  | "eventos"
  | "tarefas"
  | "relatorios"
  | "membros"
  | "administracao";

export interface Permissao {
  ler: boolean;
  escrever: boolean;
  excluir: boolean;
}

export interface Usuario {
  id: number;
  username: string;
  nome: string;
  email: string;
  cargo: string;
  foto: string | null;
  perfis: string[];
  perfil_principal: string;
  eh_admin: boolean;
  somente_leitura: boolean;
  is_superuser: boolean;
  permissoes: Record<Modulo, Permissao>;
}

export interface CredenciaisLogin {
  usuario: string;
  senha: string;
}

export interface TrocaSenha {
  senha_atual: string;
  senha_nova: string;
  senha_nova_confirmacao: string;
}
