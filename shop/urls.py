from django.urls import path

from shop.views import OrderCreateAPIView

urlpatterns = [
    path("orders/", OrderCreateAPIView.as_view(), name="order-create"),
]
