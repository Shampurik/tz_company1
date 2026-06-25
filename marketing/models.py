from django.conf import settings
from django.db import models
from django.db.models import Q

from config.django_compat import check_constraint
from shop.models import Category


class PromoCode(models.Model):
    code = models.CharField(max_length=64, unique=True)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=4)
    valid_from = models.DateTimeField(null=True, blank=True)
    valid_until = models.DateTimeField(null=True, blank=True)
    max_usages = models.PositiveIntegerField()
    used_count = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    categories = models.ManyToManyField(
        Category,
        blank=True,
        related_name="promo_codes",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["code"]
        constraints = [
            check_constraint(
                condition=Q(discount_percent__gt=0) & Q(discount_percent__lte=1),
                name="promocode_discount_percent_gt_0_lte_1",
            ),
            check_constraint(
                condition=Q(max_usages__gt=0),
                name="promocode_max_usages_gt_0",
            ),
            check_constraint(
                condition=Q(used_count__gte=0),
                name="promocode_used_count_gte_0",
            ),
        ]

    def __str__(self):
        return self.code


class PromoCodeUsage(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    promo_code = models.ForeignKey(
        PromoCode,
        on_delete=models.PROTECT,
        related_name="usages",
    )
    order = models.OneToOneField(
        "shop.Order",
        on_delete=models.CASCADE,
        related_name="promo_usage",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "promo_code"],
                name="unique_user_promo_code_usage",
            ),
        ]

    def __str__(self):
        return f"{self.user_id}:{self.promo_code_id}"


class MailingMessage(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        SENT = "sent", "Sent"
        FAILED = "failed", "Failed"

    external_id = models.CharField(max_length=255, unique=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    email = models.EmailField()
    subject = models.CharField(max_length=255)
    message = models.TextField()
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    error_message = models.TextField(blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at", "id"]

    def __str__(self):
        return f"{self.external_id}:{self.email}"
