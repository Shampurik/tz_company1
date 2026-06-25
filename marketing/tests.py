from decimal import Decimal
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.test import TransactionTestCase
from django.urls import reverse
from django.utils import timezone
from openpyxl import Workbook
from rest_framework import status
from rest_framework.test import APIClient

from marketing.models import MailingMessage, PromoCode, PromoCodeUsage
from marketing.tasks import send_mailing_message
from shop.models import Category, Good, Order


class PromoCodeOrderCreateAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(username="customer")
        self.category = Category.objects.create(name="Books", slug="books")
        self.other_category = Category.objects.create(name="Games", slug="games")
        self.good = Good.objects.create(
            category=self.category,
            name="Django Book",
            price=Decimal("100.00"),
        )
        self.other_good = Good.objects.create(
            category=self.other_category,
            name="Board Game",
            price=Decimal("200.00"),
        )
        self.url = reverse("api_v1:order-create")

    def test_create_order_with_valid_promo_code(self):
        promo = PromoCode.objects.create(
            code="SUMMER2025",
            discount_percent=Decimal("0.1000"),
            max_usages=5,
        )

        response = self.client.post(
            self.url,
            {
                "user_id": self.user.id,
                "goods": [{"good_id": self.good.id, "quantity": 2}],
                "promo_code": promo.code,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["discount"], "0.1")
        self.assertEqual(response.data["total"], 180)
        promo.refresh_from_db()
        self.assertEqual(promo.used_count, 1)
        self.assertTrue(PromoCodeUsage.objects.filter(user=self.user, promo_code=promo).exists())

    def test_unknown_promo_code_returns_400(self):
        response = self.client.post(
            self.url,
            {
                "user_id": self.user.id,
                "goods": [{"good_id": self.good.id, "quantity": 1}],
                "promo_code": "UNKNOWN",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("promo_code", response.data)

    def test_expired_promo_code_returns_400(self):
        promo = PromoCode.objects.create(
            code="OLD",
            discount_percent=Decimal("0.1000"),
            valid_until=timezone.now() - timezone.timedelta(days=1),
            max_usages=5,
        )

        response = self.client.post(
            self.url,
            {
                "user_id": self.user.id,
                "goods": [{"good_id": self.good.id, "quantity": 1}],
                "promo_code": promo.code,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Order.objects.count(), 0)

    def test_promo_usage_limit_returns_400(self):
        promo = PromoCode.objects.create(
            code="LIMIT",
            discount_percent=Decimal("0.1000"),
            max_usages=1,
            used_count=1,
        )

        response = self.client.post(
            self.url,
            {
                "user_id": self.user.id,
                "goods": [{"good_id": self.good.id, "quantity": 1}],
                "promo_code": promo.code,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Order.objects.count(), 0)

    def test_user_cannot_use_same_promo_twice(self):
        promo = PromoCode.objects.create(
            code="ONCE",
            discount_percent=Decimal("0.1000"),
            max_usages=5,
        )
        order = Order.objects.create(
            user=self.user,
            promo_code=promo,
            price=Decimal("100.00"),
            discount=Decimal("0.1000"),
            total=Decimal("90.00"),
        )
        PromoCodeUsage.objects.create(user=self.user, promo_code=promo, order=order)

        response = self.client.post(
            self.url,
            {
                "user_id": self.user.id,
                "goods": [{"good_id": self.good.id, "quantity": 1}],
                "promo_code": promo.code,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_category_restricted_promo_applies_only_to_matching_goods(self):
        promo = PromoCode.objects.create(
            code="BOOKS10",
            discount_percent=Decimal("0.1000"),
            max_usages=5,
        )
        promo.categories.add(self.category)

        response = self.client.post(
            self.url,
            {
                "user_id": self.user.id,
                "goods": [
                    {"good_id": self.good.id, "quantity": 1},
                    {"good_id": self.other_good.id, "quantity": 1},
                ],
                "promo_code": promo.code,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["price"], 300)
        self.assertEqual(response.data["total"], 290)
        self.assertEqual(response.data["goods"][0]["discount"], "0.1")
        self.assertEqual(response.data["goods"][1]["discount"], "0")

    def test_promo_does_not_apply_to_excluded_good(self):
        self.good.is_promo_excluded = True
        self.good.save(update_fields=["is_promo_excluded"])
        promo = PromoCode.objects.create(
            code="NOEXCLUDE",
            discount_percent=Decimal("0.1000"),
            max_usages=5,
        )

        response = self.client.post(
            self.url,
            {
                "user_id": self.user.id,
                "goods": [{"good_id": self.good.id, "quantity": 1}],
                "promo_code": promo.code,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["discount"], "0")
        self.assertEqual(response.data["total"], 100)


class MailingImportCommandTests(TransactionTestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="mailing-customer")

    def test_import_mailings_creates_records_skips_duplicates_and_counts_errors(self):
        with TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "mailings.xlsx"
            self._create_xlsx(
                file_path,
                [
                    ["external_id", "user_id", "email", "subject", "message"],
                    ["ext-1", self.user.id, "customer@example.com", "Hello", "First message"],
                    ["ext-1", self.user.id, "customer@example.com", "Duplicate", "Duplicate message"],
                    ["ext-2", self.user.id, "not-an-email", "Bad", "Invalid email"],
                    ["ext-3", 999999, "missing@example.com", "Bad", "Missing user"],
                ],
            )

            stdout = StringIO()
            with patch("marketing.xlsx_import.send_mailing_message.apply_async") as apply_async:
                call_command("import_mailings", str(file_path), "--countdown=7", stdout=stdout)

        self.assertEqual(MailingMessage.objects.count(), 1)
        mailing_message = MailingMessage.objects.get(external_id="ext-1")
        self.assertEqual(mailing_message.email, "customer@example.com")
        apply_async.assert_called_once_with(args=[mailing_message.id], countdown=7)
        self.assertIn("Processed rows: 4", stdout.getvalue())
        self.assertIn("Created records: 1", stdout.getvalue())
        self.assertIn("Skipped records: 1", stdout.getvalue())
        self.assertIn("Error rows: 2", stdout.getvalue())

    def test_send_mailing_message_logs_and_marks_record_as_sent(self):
        mailing_message = MailingMessage.objects.create(
            external_id="ext-send",
            user=self.user,
            email="customer@example.com",
            subject="Welcome",
            message="Delayed hello",
        )

        with self.assertLogs("marketing.tasks", level="INFO") as captured_logs:
            send_mailing_message(mailing_message.id)

        mailing_message.refresh_from_db()
        self.assertEqual(mailing_message.status, MailingMessage.Status.SENT)
        self.assertIsNotNone(mailing_message.sent_at)
        self.assertIn("Delayed email to customer@example.com", captured_logs.output[0])

    def _create_xlsx(self, file_path: Path, rows: list[list[object]]) -> None:
        workbook = Workbook()
        worksheet = workbook.active
        for row in rows:
            worksheet.append(row)
        workbook.save(file_path)
