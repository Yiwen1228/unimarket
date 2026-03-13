from rest_framework import serializers
from .models import Customer, Staff, Product, Order, OrderItem

class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ['id', 'username', 'email', 'phone_number']

class StaffSerializer(serializers.ModelSerializer):
    class Meta:
        model = Staff
        fields = ['id', 'username', 'email', 'name']

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'product_name', 'unit_price', 'stock_quantity', 'category']

class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.product_name', read_only=True)
    unit_price = serializers.DecimalField(source='product.unit_price', max_digits=8, decimal_places=2, read_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_name', 'quantity', 'unit_price']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    customer_username = serializers.CharField(source='customer.username', read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'customer', 'customer_username', 'order_time', 'total_amount', 'status', 'items']
