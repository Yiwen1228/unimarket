from rest_framework import serializers
from .models import Customer, Staff, Product, Order, OrderItem, Favorite, RefundRequest, Notification, Category

class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ['id', 'username', 'email', 'phone_number']

class StaffSerializer(serializers.ModelSerializer):
    class Meta:
        model = Staff
        fields = ['id', 'username', 'email', 'name']

class ProductSerializer(serializers.ModelSerializer):
    seller_name = serializers.CharField(source='seller.username', read_only=True, default=None)

    class Meta:
        model = Product
        fields = ['id', 'product_name', 'unit_price', 'stock_quantity', 'category', 'seller', 'seller_name', 'description', 'image', 'is_active']

class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.SerializerMethodField()
    unit_price = serializers.SerializerMethodField()
    seller_id = serializers.SerializerMethodField()
    seller_name = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_name', 'quantity', 'unit_price', 'seller_id', 'seller_name']

    def get_product_name(self, obj):
        if obj.product:
            return obj.product.product_name
        return obj.product_name_snapshot or 'Deleted Product'

    def get_unit_price(self, obj):
        if obj.product:
            return str(obj.product.unit_price)
        return str(obj.unit_price_snapshot)

    def get_seller_id(self, obj):
        if obj.product and obj.product.seller_id:
            return obj.product.seller_id
        return None

    def get_seller_name(self, obj):
        if obj.product and obj.product.seller:
            return obj.product.seller.username
        return obj.seller_name_snapshot or None

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    customer_username = serializers.CharField(source='customer.username', read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'customer', 'customer_username', 'order_time', 'total_amount', 'status', 'items']


class FavoriteSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.product_name', read_only=True)
    unit_price = serializers.DecimalField(source='product.unit_price', max_digits=10, decimal_places=2, read_only=True)
    category = serializers.CharField(source='product.category', read_only=True)

    class Meta:
        model = Favorite
        fields = ['id', 'product', 'product_name', 'unit_price', 'category', 'created_time']


class RefundRequestSerializer(serializers.ModelSerializer):
    customer_username = serializers.CharField(source='customer.username', read_only=True)
    product_name = serializers.CharField(source='order_item.product.product_name', read_only=True)
    unit_price = serializers.DecimalField(source='order_item.product.unit_price', max_digits=10, decimal_places=2, read_only=True)
    order_id = serializers.IntegerField(source='order.id', read_only=True)

    class Meta:
        model = RefundRequest
        fields = [
            'id', 'customer', 'customer_username', 'order_id',
            'order_item', 'product_name', 'unit_price', 'quantity',
            'reason', 'status', 'staff', 'created_time', 'updated_time',
        ]


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'message', 'link', 'is_read', 'created_time']


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']
