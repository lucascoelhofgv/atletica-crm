import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Link, useRouter } from "@tanstack/react-router";
import { KeyRound, LogOut, UserRound, Wrench } from "lucide-react";
import { toast } from "sonner";

import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { logout } from "@/features/auth/api";
import { useUsuario } from "@/features/auth/queries";
import { iniciais } from "@/lib/formatos";

export function MenuUsuario() {
  const usuario = useUsuario();
  const queryClient = useQueryClient();
  const router = useRouter();

  const sair = useMutation({
    mutationFn: logout,
    onSuccess: () => {
      queryClient.clear();
      router.navigate({ to: "/login", search: { voltar: undefined } });
    },
    onError: (erro: Error) => toast.error(erro.message),
  });

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" className="h-9 gap-2 px-2">
          <Avatar className="size-7">
            {usuario.foto && <AvatarImage src={usuario.foto} alt={usuario.nome} />}
            <AvatarFallback className="text-xs">{iniciais(usuario.nome)}</AvatarFallback>
          </Avatar>
          <span className="hidden max-w-40 truncate text-sm md:inline">{usuario.nome}</span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-60">
        <DropdownMenuLabel className="space-y-1">
          <div className="truncate font-medium">{usuario.nome}</div>
          <div className="flex items-center gap-2">
            <Badge variant="secondary" className="font-normal">
              {usuario.perfil_principal}
            </Badge>
            {usuario.cargo && (
              <span className="truncate text-xs text-muted-foreground">{usuario.cargo}</span>
            )}
          </div>
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuItem asChild>
          <Link to="/conta">
            <UserRound /> Meus dados
          </Link>
        </DropdownMenuItem>
        <DropdownMenuItem asChild>
          <Link to="/conta">
            <KeyRound /> Alterar senha
          </Link>
        </DropdownMenuItem>
        {usuario.eh_admin && (
          <DropdownMenuItem asChild>
            <a href="/admin/">
              <Wrench /> Admin avançado
            </a>
          </DropdownMenuItem>
        )}
        <DropdownMenuSeparator />
        <DropdownMenuItem
          variant="destructive"
          disabled={sair.isPending}
          onSelect={() => sair.mutate()}
        >
          <LogOut /> {sair.isPending ? "Saindo…" : "Sair"}
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
