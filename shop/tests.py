from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from shop.models import Category, Good


class OrderCreateAPITests(TestCase):
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

    def test_create_order_without_promo_code(self):
        response = self.client.post(
            self.url,
            {
                "user_id": self.user.id,
                "goods": [{"good_id": self.good.id, "quantity": 2}],
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["price"], 200)
        self.assertEqual(response.data["discount"], "0")
        self.assertEqual(response.data["total"], 200)
        self.assertEqual(response.data["goods"][0]["total"], 200)

    def test_unknown_user_returns_400(self):
        response = self.client.post(
            self.url,
            {
                "user_id": 999,
                "goods": [{"good_id": self.good.id, "quantity": 1}],
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("user_id", response.data)

    def test_unknown_good_returns_400(self):
        response = self.client.post(
            self.url,
            {
                "user_id": self.user.id,
                "goods": [{"good_id": 999, "quantity": 1}],
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("goods", response.data)

    def test_inactive_good_returns_400(self):
        self.good.is_active = False
        self.good.save(update_fields=["is_active"])
        response = self.client.post(
            self.url,
            {
                "user_id": self.user.id,
                "goods": [{"good_id": self.good.id, "quantity": 1}],
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("goods", response.data)

    def test_duplicate_goods_are_rejected(self):
        response = self.client.post(
            self.url,
            {
                "user_id": self.user.id,
                "goods": [
                    {"good_id": self.good.id, "quantity": 1},
                    {"good_id": self.good.id, "quantity": 2},
                ],
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("goods", response.data)
