from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.db.models import F
from django.utils import timezone
from rest_framework import serializers

from marketing.models import PromoCode, PromoCodeUsage
from shop.models import Good, Order, OrderItem

MONEY_QUANT = Decimal("0.01")
ZERO_DISCOUNT = Decimal("0")


@dataclass(frozen=True)
class CalculatedOrderItem:
    good: Good
    quantity: int
    price: Decimal
    discount: Decimal
    total: Decimal


@dataclass(frozen=True)
class CalculatedOrder:
    items: list[CalculatedOrderItem]
    price: Decimal
    discount: Decimal
    total: Decimal


def create_order(*, user_id: int, goods: list[dict], promo_code: str | None = None) -> Order:
    with transaction.atomic():
        user = _get_user(user_id)
        goods_by_id = _get_goods_by_id(goods)
        promo = _get_locked_promo(promo_code) if promo_code else None

        if promo is not None:
            _validate_promo_for_user(promo, user)

        calculation = _calculate_order(goods, goods_by_id, promo)

        order = Order.objects.create(
            user=user,
            promo_code=promo,
            price=calculation.price,
            discount=calculation.discount,
            total=calculation.total,
        )
        OrderItem.objects.bulk_create(
            [
                OrderItem(
                    order=order,
                    good=item.good,
                    quantity=item.quantity,
                    price=item.price,
                    discount=item.discount,
                    total=item.total,
                )
                for item in calculation.items
            ]
        )

        if promo is not None:
            try:
                PromoCodeUsage.objects.create(user=user, promo_code=promo, order=order)
            except IntegrityError as exc:
                raise serializers.ValidationError(
                    {"promo_code": "User has already used this promo code."}
                ) from exc
            PromoCode.objects.filter(pk=promo.pk).update(used_count=F("used_count") + 1)

        return Order.objects.prefetch_related("items").get(pk=order.pk)


def _get_user(user_id: int):
    user_model = get_user_model()
    try:
        return user_model.objects.get(pk=user_id)
    except user_model.DoesNotExist as exc:
        raise serializers.ValidationError({"user_id": "User does not exist."}) from exc


def _get_goods_by_id(goods_payload: list[dict]) -> dict[int, Good]:
    requested_ids = [item["good_id"] for item in goods_payload]
    goods = Good.objects.select_related("category").filter(id__in=requested_ids, is_active=True)
    goods_by_id = {good.id: good for good in goods}
    missing_ids = sorted(set(requested_ids) - set(goods_by_id))

    if missing_ids:
        raise serializers.ValidationError(
            {"goods": f"Goods do not exist or are inactive: {missing_ids}."}
        )

    return goods_by_id


def _get_locked_promo(promo_code: str) -> PromoCode:
    normalized_code = promo_code.strip()
    try:
        return PromoCode.objects.select_for_update().prefetch_related("categories").get(
            code=normalized_code,
        )
    except PromoCode.DoesNotExist as exc:
        raise serializers.ValidationError({"promo_code": "Promo code does not exist."}) from exc


def _validate_promo_for_user(promo: PromoCode, user) -> None:
    now = timezone.now()

    if not promo.is_active:
        raise serializers.ValidationError({"promo_code": "Promo code is inactive."})

    if promo.valid_from and promo.valid_from > now:
        raise serializers.ValidationError({"promo_code": "Promo code is not active yet."})

    if promo.valid_until and promo.valid_until < now:
        raise serializers.ValidationError({"promo_code": "Promo code has expired."})

    if promo.used_count >= promo.max_usages:
        raise serializers.ValidationError({"promo_code": "Promo code usage limit exceeded."})

    if PromoCodeUsage.objects.filter(user=user, promo_code=promo).exists():
        raise serializers.ValidationError({"promo_code": "User has already used this promo code."})


def _calculate_order(
    goods_payload: list[dict],
    goods_by_id: dict[int, Good],
    promo: PromoCode | None,
) -> CalculatedOrder:
    promo_category_ids = set()
    if promo is not None:
        promo_category_ids = set(promo.categories.values_list("id", flat=True))

    items = []
    order_price = Decimal("0.00")
    order_total = Decimal("0.00")
    any_discount_applied = False

    for payload_item in goods_payload:
        good = goods_by_id[payload_item["good_id"]]
        quantity = payload_item["quantity"]
        item_price = good.price
        item_discount = _get_item_discount(good, promo, promo_category_ids)
        item_base_total = _to_money(item_price * quantity)
        item_total = _to_money(item_base_total * (Decimal("1") - item_discount))

        if item_discount > ZERO_DISCOUNT:
            any_discount_applied = True

        order_price += item_base_total
        order_total += item_total
        items.append(
            CalculatedOrderItem(
                good=good,
                quantity=quantity,
                price=item_price,
                discount=item_discount,
                total=item_total,
            )
        )

    order_discount = promo.discount_percent if promo is not None and any_discount_applied else ZERO_DISCOUNT

    return CalculatedOrder(
        items=items,
        price=_to_money(order_price),
        discount=order_discount,
        total=_to_money(order_total),
    )


def _get_item_discount(
    good: Good,
    promo: PromoCode | None,
    promo_category_ids: set[int],
) -> Decimal:
    if promo is None:
        return ZERO_DISCOUNT

    if good.is_promo_excluded:
        return ZERO_DISCOUNT

    if promo_category_ids and good.category_id not in promo_category_ids:
        return ZERO_DISCOUNT

    return promo.discount_percent


def _to_money(value: Decimal) -> Decimal:
    return value.quantize(MONEY_QUANT, rounding=ROUND_HALF_UP)
