# Generated manually for the test assignment.

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

from config.django_compat import check_constraint


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Category",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=255)),
                ("slug", models.SlugField(max_length=255, unique=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ["name"],
                "verbose_name_plural": "categories",
            },
        ),
        migrations.CreateModel(
            name="Order",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("created", "Created"),
                            ("delivered", "Delivered"),
                            ("cancelled", "Cancelled"),
                        ],
                        default="created",
                        max_length=32,
                    ),
                ),
                ("price", models.DecimalField(decimal_places=2, max_digits=12)),
                ("discount", models.DecimalField(decimal_places=4, default=0, max_digits=5)),
                ("total", models.DecimalField(decimal_places=2, max_digits=12)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="orders",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at", "-id"],
            },
        ),
        migrations.CreateModel(
            name="Good",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=255)),
                ("price", models.DecimalField(decimal_places=2, max_digits=12)),
                ("is_promo_excluded", models.BooleanField(default=False)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "category",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="goods",
                        to="shop.category",
                    ),
                ),
            ],
            options={
                "ordering": ["name"],
            },
        ),
        migrations.AddConstraint(
            model_name="order",
            constraint=check_constraint(condition=models.Q(("price__gte", 0)), name="order_price_gte_0"),
        ),
        migrations.AddConstraint(
            model_name="order",
            constraint=check_constraint(condition=models.Q(("total__gte", 0)), name="order_total_gte_0"),
        ),
        migrations.AddConstraint(
            model_name="order",
            constraint=check_constraint(
                condition=models.Q(("discount__gte", 0), ("discount__lte", 1)),
                name="order_discount_gte_0_lte_1",
            ),
        ),
        migrations.AddConstraint(
            model_name="good",
            constraint=check_constraint(condition=models.Q(("price__gte", 0)), name="shop_good_price_gte_0"),
        ),
    ]
