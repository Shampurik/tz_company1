# Generated manually for the test assignment.

from django.db import migrations, models
import django.db.models.deletion

from config.django_compat import check_constraint


class Migration(migrations.Migration):
    dependencies = [
        ("marketing", "0001_initial"),
        ("shop", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="order",
            name="promo_code",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="orders",
                to="marketing.promocode",
            ),
        ),
        migrations.CreateModel(
            name="OrderItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("quantity", models.PositiveIntegerField()),
                ("price", models.DecimalField(decimal_places=2, max_digits=12)),
                ("discount", models.DecimalField(decimal_places=4, default=0, max_digits=5)),
                ("total", models.DecimalField(decimal_places=2, max_digits=12)),
                (
                    "good",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="order_items",
                        to="shop.good",
                    ),
                ),
                (
                    "order",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="items",
                        to="shop.order",
                    ),
                ),
            ],
            options={
                "ordering": ["id"],
            },
        ),
        migrations.AddConstraint(
            model_name="orderitem",
            constraint=check_constraint(condition=models.Q(("quantity__gt", 0)), name="order_item_quantity_gt_0"),
        ),
        migrations.AddConstraint(
            model_name="orderitem",
            constraint=check_constraint(condition=models.Q(("price__gte", 0)), name="order_item_price_gte_0"),
        ),
        migrations.AddConstraint(
            model_name="orderitem",
            constraint=check_constraint(condition=models.Q(("total__gte", 0)), name="order_item_total_gte_0"),
        ),
        migrations.AddConstraint(
            model_name="orderitem",
            constraint=check_constraint(
                condition=models.Q(("discount__gte", 0), ("discount__lte", 1)),
                name="order_item_discount_gte_0_lte_1",
            ),
        ),
    ]
