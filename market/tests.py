from django.test import TestCase, Client
from django.contrib.auth.hashers import make_password
from .models import Customer, Staff, Product, Order, OrderItem
import json

class CustomerAuthTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.customer = Customer.objects.create(
            username='testuser',
            email='test@test.com',
            password=make_password('Test123!'),
            phone_number='1234567890'
        )

    def test_customer_register(self):
        response = self.client.post('/api/customer/register/',
            data=json.dumps({'userId': 'newuser', 'email': 'new@test.com', 'password': 'Pass123!'}),
            content_type='application/json')
        self.assertEqual(response.status_code, 201)

    def test_customer_register_duplicate_email(self):
        response = self.client.post('/api/customer/register/',
            data=json.dumps({'userId': 'anotheruser', 'email': 'test@test.com', 'password': 'Pass123!'}),
            content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_customer_login_success(self):
        response = self.client.post('/api/customer/login/',
            data=json.dumps({'email': 'test@test.com', 'password': 'Test123!'}),
            content_type='application/json')
        self.assertEqual(response.status_code, 200)

    def test_customer_login_wrong_password(self):
        response = self.client.post('/api/customer/login/',
            data=json.dumps({'email': 'test@test.com', 'password': 'wrongpass'}),
            content_type='application/json')
        self.assertEqual(response.status_code, 401)

class StaffAuthTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.staff = Staff.objects.create(
            username='staffuser',
            email='staff@test.com',
            password=make_password('Staff123!')
        )

    def test_staff_login_success(self):
        response = self.client.post('/api/staff/login/',
            data=json.dumps({'email': 'staff@test.com', 'password': 'Staff123!'}),
            content_type='application/json')
        self.assertEqual(response.status_code, 200)

    def test_staff_login_wrong_password(self):
        response = self.client.post('/api/staff/login/',
            data=json.dumps({'email': 'staff@test.com', 'password': 'wrongpass'}),
            content_type='application/json')
        self.assertEqual(response.status_code, 401)

class ProductTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.product = Product.objects.create(
            product_name='Test Milk',
            category='Dairy',
            unit_price=1.20,
            stock_quantity=10
        )

    def test_product_list(self):
        response = self.client.get('/api/products/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

class OrderTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.customer = Customer.objects.create(
            username='orderuser',
            email='order@test.com',
            password=make_password('Order123!')
        )
        self.product = Product.objects.create(
            product_name='Test Product',
            category='Test',
            unit_price=2.00,
            stock_quantity=10
        )
        session = self.client.session
        session['customer_id'] = self.customer.id
        session['role'] = 'customer'
        session.save()

    def test_place_order(self):
        response = self.client.post('/api/orders/',
            data=json.dumps({'items': [{'productId': self.product.id, 'qty': 2}]}),
            content_type='application/json')
        self.assertEqual(response.status_code, 201)

    def test_place_order_exceeds_stock(self):
        response = self.client.post('/api/orders/',
            data=json.dumps({'items': [{'productId': self.product.id, 'qty': 999}]}),
            content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_my_orders(self):
        response = self.client.get('/api/orders/my/')
        self.assertEqual(response.status_code, 200)
