from django.core.management.base import BaseCommand
from django.db import transaction

from producao.models import Lote, LoteDiario


class Command(BaseCommand):
    help = (
        "Audita (e opcionalmente corrige) registros de LoteDiario anteriores ao "
        "data_povoamento do lote."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--lote-id",
            type=int,
            default=None,
            help="Filtra auditoria para um lote especifico.",
        )
        parser.add_argument(
            "--fix",
            action="store_true",
            help="Aplica correcoes removendo LoteDiario anterior ao data_povoamento.",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=20,
            help="Quantidade maxima de linhas de exemplo no relatorio (default: 20).",
        )

    def handle(self, *args, **options):
        lote_id = options["lote_id"]
        apply_fix = options["fix"]
        limit = options["limit"]

        lotes = Lote.objects.all().order_by("id")
        if lote_id:
            lotes = lotes.filter(id=lote_id)

        if not lotes.exists():
            self.stdout.write(self.style.WARNING("Nenhum lote encontrado para os filtros informados."))
            return

        affected = []
        total_legacy = 0

        for lote in lotes:
            if not lote.data_povoamento:
                continue

            legacy_qs = LoteDiario.objects.filter(
                lote=lote,
                data_evento__lt=lote.data_povoamento,
            ).order_by("data_evento")

            count = legacy_qs.count()
            if count == 0:
                continue

            total_legacy += count
            first_date = legacy_qs.first().data_evento
            last_date = legacy_qs.last().data_evento

            affected.append(
                {
                    "lote_id": lote.id,
                    "lote_nome": lote.nome,
                    "data_povoamento": lote.data_povoamento,
                    "legacy_count": count,
                    "first_date": first_date,
                    "last_date": last_date,
                }
            )

        if not affected:
            self.stdout.write(self.style.SUCCESS("Nenhum LoteDiario legado encontrado."))
            return

        self.stdout.write(self.style.WARNING("Lotes com LoteDiario anterior ao data_povoamento:"))
        for row in affected[:limit]:
            self.stdout.write(
                f"- lote_id={row['lote_id']} | lote={row['lote_nome']} | "
                f"povoamento={row['data_povoamento']} | legacy={row['legacy_count']} | "
                f"periodo={row['first_date']}..{row['last_date']}"
            )

        self.stdout.write("\nResumo:")
        self.stdout.write(f"- lotes_afetados: {len(affected)}")
        self.stdout.write(f"- registros_legados: {total_legacy}")

        if not apply_fix:
            self.stdout.write(
                self.style.WARNING(
                    "Modo auditoria (sem alteracoes). Rode com --fix para aplicar limpeza."
                )
            )
            return

        with transaction.atomic():
            deleted_total = 0
            for row in affected:
                deleted_count, _ = LoteDiario.objects.filter(
                    lote_id=row["lote_id"],
                    data_evento__lt=row["data_povoamento"],
                ).delete()
                deleted_total += deleted_count

        self.stdout.write(self.style.SUCCESS("\nCorrecao aplicada com sucesso."))
        self.stdout.write(f"- registros_excluidos: {deleted_total}")
