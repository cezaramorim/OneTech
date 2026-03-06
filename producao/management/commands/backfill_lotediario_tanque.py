from django.core.management.base import BaseCommand
from django.db import transaction

from producao.models import LoteDiario
from producao.utils import construir_resolvedor_tanque_lote


class Command(BaseCommand):
    help = (
        "Preenche snapshot historico de tanque em LoteDiario.tanque para "
        "registros nulos, com base na data_evento."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--lote-id",
            type=int,
            default=None,
            help="Filtra processamento para um lote especifico.",
        )
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Aplica o backfill. Sem --apply roda apenas auditoria.",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=20,
            help="Quantidade maxima de exemplos exibidos no relatorio.",
        )

    def handle(self, *args, **options):
        lote_id = options["lote_id"]
        apply_changes = options["apply"]
        limit = options["limit"]

        qs = LoteDiario.objects.filter(tanque__isnull=True).select_related("lote").order_by("lote_id", "data_evento", "id")
        if lote_id:
            qs = qs.filter(lote_id=lote_id)

        total = qs.count()
        if total == 0:
            self.stdout.write(self.style.SUCCESS("Nenhum LoteDiario com tanque nulo encontrado."))
            return

        to_update = []
        exemplos = []
        lote_id_atual = None
        resolver_atual = None

        for ld in qs.iterator():
            if ld.lote_id != lote_id_atual:
                lote_id_atual = ld.lote_id
                resolver_atual = construir_resolvedor_tanque_lote(ld.lote)

            tanque = resolver_atual(ld.data_evento) if resolver_atual else None
            if tanque is None:
                continue
            to_update.append((ld.id, tanque.id, ld.lote_id, ld.data_evento, ld.lote.nome, tanque.nome))
            if len(exemplos) < limit:
                exemplos.append((ld.id, ld.lote.nome, ld.data_evento, tanque.nome))

        self.stdout.write(self.style.WARNING("Auditoria de backfill de tanque em LoteDiario:"))
        self.stdout.write(f"- candidatos_tanque_nulo: {total}")
        self.stdout.write(f"- elegiveis_para_preencher: {len(to_update)}")
        self.stdout.write(f"- permanecem_nulos: {total - len(to_update)}")

        if exemplos:
            self.stdout.write("Exemplos:")
            for ld_id, lote_nome, data_evento, tanque_nome in exemplos:
                self.stdout.write(
                    f"- ld_id={ld_id} | lote={lote_nome} | data={data_evento} | tanque_resolvido={tanque_nome}"
                )

        if not apply_changes:
            self.stdout.write(
                self.style.WARNING("Modo auditoria (sem alteracoes). Rode com --apply para gravar.")
            )
            return

        updated = 0
        with transaction.atomic():
            for ld_id, tanque_id, *_ in to_update:
                updated += LoteDiario.objects.filter(id=ld_id, tanque__isnull=True).update(tanque_id=tanque_id)

        self.stdout.write(self.style.SUCCESS("Backfill aplicado com sucesso."))
        self.stdout.write(f"- registros_atualizados: {updated}")
