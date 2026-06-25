# Generated manually for the test assignment.

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("marketing", "0001_initial"),
        ("shop", "0002_order_promo_code_orderitem"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="PromoCodeUsage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "order",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="promo_usage",
                        to="shop.order",
                    ),
                ),
                (
                    "promo_code",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="usages",
                        to="marketing.promocode",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
                ),
            ],
        ),
        migrations.AddConstraint(
            model_name="promocodeusage",
            constraint=models.UniqueConstraint(
                fields=("user", "promo_code"),
                name="unique_user_promo_code_usage",
            ),
        ),
    ]
