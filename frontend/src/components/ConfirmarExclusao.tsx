import { LoaderCircle, Trash2 } from "lucide-react";
import { useState } from "react";

import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";

export function ConfirmarExclusao({
  titulo,
  descricao,
  aoConfirmar,
  pendente,
  rotuloBotao = "Excluir",
  variante = "outline",
}: {
  titulo: string;
  descricao: string;
  aoConfirmar: () => void | Promise<unknown>;
  pendente?: boolean;
  rotuloBotao?: string;
  variante?: "outline" | "ghost" | "destructive";
}) {
  const [aberto, setAberto] = useState(false);
  return (
    <AlertDialog open={aberto} onOpenChange={setAberto}>
      <AlertDialogTrigger asChild>
        <Button variant={variante} size="sm" className="text-destructive hover:text-destructive">
          <Trash2 /> {rotuloBotao}
        </Button>
      </AlertDialogTrigger>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>{titulo}</AlertDialogTitle>
          <AlertDialogDescription>{descricao}</AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel>Cancelar</AlertDialogCancel>
          <AlertDialogAction
            className="bg-destructive text-white hover:bg-destructive/90"
            disabled={pendente}
            onClick={(e) => {
              e.preventDefault();
              void Promise.resolve(aoConfirmar()).then(() => setAberto(false));
            }}
          >
            {pendente && <LoaderCircle className="animate-spin" />}
            Excluir
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
