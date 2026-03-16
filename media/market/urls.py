from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.customer_register, name='customer_register'),
    path('login/', views.customer_login, name='customer_login'),
    path('logout/', views.customer_logout, name='customer_logout'),
    path('verify/', views.verify_email, name='verify_email'),
    path('profile/', views.profile, name='profile'),
    path('products/', views.products, name='products'),
    path('orders/', views.my_orders, name='my_orders'),
    path('favorites/', views.favorites, name='favorites'),
    path('chat/', views.chat, name='chat'),
    path('staff/login/', views.staff_login, name='staff_login'),
    path('staff/logout/', views.staff_logout, name='staff_logout'),
    path('staff/dashboard/', views.staff_dashboard, name='staff_dashboard'),
    path('staff/orders/', views.staff_orders, name='staff_orders'),
    path('staff/inventory/', views.staff_inventory, name='staff_inventory'),
    path('staff/chat/', views.staff_chat, name='staff_chat'),
    path('refunds/', views.my_refunds_page, name='my_refunds'),
    path('staff/refunds/', views.staff_refunds_page, name='staff_refunds'),
    path('about/', views.about_us, name='about_us'),
    path('contact/', views.contact, name='contact'),
    path('policy/', views.policy, name='policy'),
]
