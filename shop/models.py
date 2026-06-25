from django.conf import settings
from django.db import models
from django.db.models import Q

from config.django_compat import check_constraint


class Category(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name


class Good(models.Model):
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="goods",
    )
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    is_promo_excluded = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            check_constraint(
                condition=Q(price__gte=0),
                name="shop_good_price_gte_0",
            ),
        ]

    def __str__(self):
        return self.name


class Order(models.Model):
    STATUS_CREATED = "created"

    STATUS_CHOICES = [
        (STATUS_CREATED, "Created"),
        ("delivered", "Delivered"),
        ("cancelled", "Cancelled"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="orders",
    )
    promo_code = models.ForeignKey(
        "marketing.PromoCode",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="orders",
    )
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default=STATUS_CREATED)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    discount = models.DecimalField(max_digits=5, decimal_places=4, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        constraints = [
            check_constraint(condition=Q(price__gte=0), name="order_price_gte_0"),
            check_constraint(condition=Q(total__gte=0), name="order_total_gte_0"),
            check_constraint(
                condition=Q(discount__gte=0) & Q(discount__lte=1),
                name="order_discount_gte_0_lte_1",
            ),
        ]

    def __str__(self):
        return f"Order #{self.pk}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    good = models.ForeignKey(Good, on_delete=models.PROTECT, related_name="order_items")
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=12, decimal_places=2)
    discount = models.DecimalField(max_digits=5, decimal_places=4, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        ordering = ["id"]
        constraints = [
            check_constraint(condition=Q(quantity__gt=0), name="order_item_quantity_gt_0"),
            check_constraint(condition=Q(price__gte=0), name="order_item_price_gte_0"),
            check_constraint(condition=Q(total__gte=0), name="order_item_total_gte_0"),
            check_constraint(
                condition=Q(discount__gte=0) & Q(discount__lte=1),
                name="order_item_discount_gte_0_lte_1",
            ),
        ]

    def __str__(self):
        return f"{self.good_id} x {self.quantity}"
