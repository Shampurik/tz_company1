from django.contrib import admin

from marketing.models import MailingMessage, PromoCode, PromoCodeUsage


@admin.register(PromoCode)
class PromoCodeAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "code",
        "discount_percent",
        "max_usages",
        "used_count",
        "is_active",
        "valid_from",
        "valid_until",
    )
    list_filter = ("is_active", "categories")
    search_fields = ("code",)
    filter_horizontal = ("categories",)


@admin.register(PromoCodeUsage)
class PromoCodeUsageAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "promo_code", "order", "created_at")
    list_filter = ("promo_code",)
    search_fields = ("promo_code__code", "user__username")


@admin.register(MailingMessage)
class MailingMessageAdmin(admin.ModelAdmin):
    list_display = ("id", "external_id", "user", "email", "subject", "status", "created_at", "sent_at")
    list_filter = ("status", "created_at", "sent_at")
    search_fields = ("external_id", "email", "subject", "user__username")
    readonly_fields = ("created_at", "updated_at", "sent_at")
