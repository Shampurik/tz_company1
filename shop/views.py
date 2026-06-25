from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from shop.serializers import OrderCreateSerializer, OrderDetailSerializer
from shop.services import create_order


class OrderCreateAPIView(APIView):
    def post(self, request):
        serializer = OrderCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        order = create_order(**serializer.validated_data)

        response_serializer = OrderDetailSerializer(order)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
