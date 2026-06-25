from django.contrib import admin

from shop.models import Category, Good, Order, OrderItem


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "slug")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Good)
class GoodAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "category", "price", "is_promo_excluded", "is_active")
    list_filter = ("category", "is_promo_excluded", "is_active")
    search_fields = ("name",)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("good", "quantity", "price", "discount", "total")
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "promo_code", "status", "price", "discount", "total", "created_at")
    list_filter = ("status", "promo_code")
    search_fields = ("id", "user__username", "promo_code__code")
    inlines = (OrderItemInline,)
