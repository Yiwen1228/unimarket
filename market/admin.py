from django.contrib import admin
from .models import Customer, Staff, Product, Order, OrderItem, Favorite, RefundRequest, Notification, Category, ChatMessage

admin.site.register(Customer)
admin.site.register(Staff)
admin.site.register(Product)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(Favorite)
admin.site.register(RefundRequest)
admin.site.register(Notification)
admin.site.register(Category)
admin.site.register(ChatMessage)
