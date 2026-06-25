from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from marketing.xlsx_import import MailingImportError, import_mailing_messages


class Command(BaseCommand):
    help = "Import mailing messages from an XLSX file and schedule delayed email sending."

    def add_arguments(self, parser):
        parser.add_argument("file_path", help="Path to the XLSX file.")
        parser.add_argument("--sheet", dest="sheet_name", help="Worksheet name. Defaults to the active sheet.")
        parser.add_argument(
            "--countdown",
            type=int,
            default=settings.MARKETING_EMAIL_SEND_DELAY_SECONDS,
            help="Delay in seconds before sending each email task.",
        )

    def handle(self, *args, **options):
        try:
            stats = import_mailing_messages(
                options["file_path"],
                sheet_name=options["sheet_name"],
                send_countdown=options["countdown"],
            )
        except MailingImportError as exc:
            raise CommandError(str(exc)) from exc

        self.stdout.write(f"Processed rows: {stats.processed_rows}")
        self.stdout.write(f"Created records: {stats.created_records}")
        self.stdout.write(f"Skipped records: {stats.skipped_records}")
        self.stdout.write(f"Error rows: {stats.error_rows}")
