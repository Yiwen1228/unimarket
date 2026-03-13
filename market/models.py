from django.db import models

class Customer(models.Model):
    username = models.CharField(max_length=100, unique=True)
    email = models.EmailField(max_length=200, unique=True, default='')
    password = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return self.username

class Staff(models.Model):
    username = models.CharField(max_length=100, unique=True)
    email = models.EmailField(max_length=200, unique=True, default='')
    name = models.CharField(max_length=100, blank=True)
    password = models.CharField(max_length=255)

    def __str__(self):
        return self.username

class Product(models.Model):
    product_name = models.CharField(max_length=200)
    category = models.CharField(max_length=100, default='General')
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.IntegerField(default=0)

    def __str__(self):
        return self.product_name

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    staff = models.ForeignKey(Staff, on_delete=models.SET_NULL, null=True, blank=True)
    order_time = models.DateTimeField(auto_now_add=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    def __str__(self):
        return f"Order {self.id} by {self.customer}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} x {self.product}"

class Favorite(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    created_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.customer} - {self.product}"
