from django.urls import path
from . import api_views

urlpatterns = [
    path('customer/register/', api_views.customer_register, name='api_customer_register'),
    path('customer/login/', api_views.customer_login, name='api_customer_login'),
    path('staff/register/', api_views.staff_register, name='api_staff_register'),
    path('staff/login/', api_views.staff_login, name='api_staff_login'),
    path('logout/', api_views.logout, name='api_logout'),
    path('products/', api_views.product_list, name='api_products'),
    path('orders/', api_views.place_order, name='api_place_order'),
    path('orders/my/', api_views.my_orders, name='api_my_orders'),
    path('staff/orders/', api_views.staff_orders, name='api_staff_orders'),
    path('staff/orders/<int:order_id>/', api_views.update_order_status, name='api_update_order'),
    path('staff/inventory/', api_views.inventory, name='api_inventory'),
    path('staff/inventory/<int:product_id>/', api_views.update_inventory, name='api_update_inventory'),
]
