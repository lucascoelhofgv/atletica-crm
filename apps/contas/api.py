"""``/api/membros/`` (gestão de acessos)."""

from django.contrib.auth.models import Group
from django.db.models import Q
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.api.permissions import PerfilModulo
from apps.nucleo.models import registrar_atividade

from .models import Membro
from .serializers import MembroSerializer, OpcoesMembroSerializer


class MembroViewSet(viewsets.ModelViewSet):
    modulo = "membros"
    permission_classes = [IsAuthenticated, PerfilModulo]
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    serializer_class = MembroSerializer
    filterset_fields = ["is_active", "groups"]
    ordering_fields = ["first_name", "username", "date_joined", "last_login"]
    ordering = ["-is_active", "first_name", "username"]
    http_method_names = ["get", "post", "patch", "head", "options"]  # sem DELETE: membro é desativado

    def get_queryset(self):
        qs = Membro.objects.prefetch_related("groups")
        termo = self.request.query_params.get("q", "").strip()
        if termo:
            qs = qs.filter(Q(username__icontains=termo) | Q(first_name__icontains=termo)
                           | Q(last_name__icontains=termo) | Q(email__icontains=termo))
        return qs

    def filter_queryset(self, queryset):
        for backend in self.filter_backends:
            if backend.__name__ == "SearchFilter":
                continue
            queryset = backend().filter_queryset(self.request, queryset, self)
        return queryset

    def perform_create(self, serializer):
        m = serializer.save()
        registrar_atividade(self.request.user, "criou membro", m.nome_exibicao, url=f"/administracao/membros")

    def perform_update(self, serializer):
        if serializer.instance == self.request.user and serializer.validated_data.get("is_active") is False:
            raise ValidationError({"is_active": ["Você não pode desativar a própria conta."]})
        m = serializer.save()
        registrar_atividade(self.request.user, "editou membro", m.nome_exibicao, url=f"/administracao/membros")

    @action(detail=False, methods=["get"])
    def opcoes(self, request):
        return Response(OpcoesMembroSerializer({"grupos": Group.objects.order_by("name")}).data)

    @action(detail=True, methods=["post"])
    def alternar(self, request, pk=None):
        m = self.get_object()
        if m == request.user:
            raise ValidationError({"non_field_errors": ["Você não pode desativar a própria conta."]})
        m.is_active = not m.is_active
        if not m.is_active and not m.data_saida:
            m.data_saida = timezone.localdate()
        m.save(update_fields=["is_active", "data_saida"])
        registrar_atividade(request.user, "desativou membro" if not m.is_active else "reativou membro",
                            m.nome_exibicao, url="/administracao/membros")
        return Response(MembroSerializer(m, context={"request": request}).data)

    @action(detail=True, methods=["post"])
    def foto(self, request, pk=None):
        m = self.get_object()
        arquivo = request.FILES.get("foto")
        if arquivo is None:
            m.foto.delete(save=False)
            m.foto = None
        else:
            m.foto = arquivo
        m.save(update_fields=["foto"])
        return Response(MembroSerializer(m, context={"request": request}).data, status=status.HTTP_200_OK)


def registrar(router):
    router.register("membros", MembroViewSet, basename="membro")
