from decimal import Decimal

from rest_framework import serializers

from shop.models import Order, OrderItem


class CompactDecimalField(serializers.DecimalField):
    def to_representation(self, value):
        if value is None:
            return None
        decimal_value = Decimal(value).normalize()
        return format(decimal_value, "f")


class MoneyField(serializers.DecimalField):
    def to_representation(self, value):
        decimal_value = Decimal(value)
        if decimal_value == decimal_value.to_integral_value():
            return int(decimal_value)
        return float(decimal_value)


class OrderGoodInputSerializer(serializers.Serializer):
    good_id = serializers.IntegerField(min_value=1)
    quantity = serializers.IntegerField(min_value=1)


class OrderCreateSerializer(serializers.Serializer):
    user_id = serializers.IntegerField(min_value=1)
    goods = OrderGoodInputSerializer(many=True)
    promo_code = serializers.CharField(required=False, allow_blank=False, trim_whitespace=True)

    def validate_goods(self, value):
        if not value:
            raise serializers.ValidationError("Goods list must not be empty.")

        good_ids = [item["good_id"] for item in value]
        if len(good_ids) != len(set(good_ids)):
            raise serializers.ValidationError("Duplicate goods are not allowed.")

        return value


class OrderItemDetailSerializer(serializers.ModelSerializer):
    good_id = serializers.IntegerField()
    price = MoneyField(max_digits=12, decimal_places=2)
    discount = CompactDecimalField(max_digits=5, decimal_places=4)
    total = MoneyField(max_digits=12, decimal_places=2)

    class Meta:
        model = OrderItem
        fields = ("good_id", "quantity", "price", "discount", "total")


class OrderDetailSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField()
    order_id = serializers.IntegerField(source="id")
    goods = OrderItemDetailSerializer(source="items", many=True)
    price = MoneyField(max_digits=12, decimal_places=2)
    discount = CompactDecimalField(max_digits=5, decimal_places=4)
    total = MoneyField(max_digits=12, decimal_places=2)

    class Meta:
        model = Order
        fields = ("user_id", "order_id", "goods", "price", "discount", "total")
