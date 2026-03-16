from django.db import models

class Customer(models.Model):
    username = models.CharField(max_length=100, unique=True)
    email = models.EmailField(max_length=200, unique=True, default='')
    password = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20, blank=True)
    is_verified = models.BooleanField(default=False)
    verification_token = models.CharField(max_length=64, blank=True, default='')
    password_reset_token = models.CharField(max_length=64, blank=True, default='')
    password_reset_expires = models.DateTimeField(null=True, blank=True)

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
    seller = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    description = models.TextField(blank=True, default='')
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    is_active = models.BooleanField(default=True)  # Staff can delist products

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
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    product_name_snapshot = models.CharField(max_length=200, default='')
    unit_price_snapshot = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    seller_name_snapshot = models.CharField(max_length=100, default='')
    quantity = models.IntegerField(default=1)

    def __str__(self):
        name = self.product_name_snapshot or (self.product.product_name if self.product else 'Deleted')
        return f"{self.quantity} x {name}"

class Favorite(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    created_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.customer} - {self.product}"

class RefundRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    order_item = models.ForeignKey(OrderItem, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    reason = models.TextField(blank=True, default='')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    staff = models.ForeignKey(Staff, on_delete=models.SET_NULL, null=True, blank=True)
    created_time = models.DateTimeField(auto_now_add=True)
    updated_time = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Refund #{self.id} - Order #{self.order.id} ({self.status})"


class Notification(models.Model):
    RECIPIENT_CHOICES = [('customer', 'Customer'), ('staff', 'Staff')]
    recipient_type = models.CharField(max_length=10, choices=RECIPIENT_CHOICES)
    recipient_id = models.IntegerField()
    message = models.TextField()
    link = models.CharField(max_length=200, blank=True, default='')
    is_read = models.BooleanField(default=False)
    created_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_time']

    def __str__(self):
        return f"Notif → {self.recipient_type}#{self.recipient_id}: {self.message[:50]}"


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name_plural = 'categories'

    def __str__(self):
        return self.name


class ChatMessage(models.Model):
    room_name = models.CharField(max_length=200, db_index=True)
    sender = models.CharField(max_length=100)
    role = models.CharField(max_length=20, default='customer')
    message = models.TextField()
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"[{self.room_name}] {self.sender}: {self.message[:50]}"
