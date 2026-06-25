# Generated manually for the test assignment.

from django.conf import settings
from django.db import migrations, models

from config.django_compat import check_constraint


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("shop", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="PromoCode",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.CharField(max_length=64, unique=True)),
                ("discount_percent", models.DecimalField(decimal_places=4, max_digits=5)),
                ("valid_from", models.DateTimeField(blank=True, null=True)),
                ("valid_until", models.DateTimeField(blank=True, null=True)),
                ("max_usages", models.PositiveIntegerField()),
                ("used_count", models.PositiveIntegerField(default=0)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "categories",
                    models.ManyToManyField(blank=True, related_name="promo_codes", to="shop.category"),
                ),
            ],
            options={
                "ordering": ["code"],
            },
        ),
        migrations.AddConstraint(
            model_name="promocode",
            constraint=check_constraint(
                condition=models.Q(("discount_percent__gt", 0), ("discount_percent__lte", 1)),
                name="promocode_discount_percent_gt_0_lte_1",
            ),
        ),
        migrations.AddConstraint(
            model_name="promocode",
            constraint=check_constraint(condition=models.Q(("max_usages__gt", 0)), name="promocode_max_usages_gt_0"),
        ),
        migrations.AddConstraint(
            model_name="promocode",
            constraint=check_constraint(condition=models.Q(("used_count__gte", 0)), name="promocode_used_count_gte_0"),
        ),
    ]
