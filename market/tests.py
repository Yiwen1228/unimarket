from django.test import TestCase, Client
from django.contrib.auth.hashers import make_password, check_password
from django.core import mail
from django.utils import timezone
from datetime import timedelta
from .models import Customer, Staff, Product, Order, OrderItem, Favorite, RefundRequest, Notification, ChatMessage
import json


class CustomerAuthTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.customer = Customer.objects.create(
            username='testuser',
            email='test@test.com',
            password=make_password('Test123!'),
            phone_number='1234567890',
            is_verified=True
        )

    def test_customer_register(self):
        response = self.client.post('/api/customer/register/',
            data=json.dumps({'userId': 'newuser', 'email': 'new@test.com', 'password': 'Pass123!'}),
            content_type='application/json')
        self.assertEqual(response.status_code, 201)
        customer = Customer.objects.get(username='newuser')
        self.assertFalse(customer.is_verified)
        self.assertTrue(len(customer.verification_token) > 0)

    def test_customer_register_duplicate_email(self):
        response = self.client.post('/api/customer/register/',
            data=json.dumps({'userId': 'anotheruser', 'email': 'test@test.com', 'password': 'Pass123!'}),
            content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_customer_register_missing_fields(self):
        response = self.client.post('/api/customer/register/',
            data=json.dumps({'userId': 'user1'}),
            content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_customer_register_weak_password(self):
        response = self.client.post('/api/customer/register/',
            data=json.dumps({'userId': 'weakuser', 'email': 'weak@test.com', 'password': 'abc'}),
            content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('8 characters', response.json()['error'])

    def test_customer_register_password_no_digit(self):
        response = self.client.post('/api/customer/register/',
            data=json.dumps({'userId': 'nodigit', 'email': 'nodigit@test.com', 'password': 'abcdefgh'}),
            content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('digit', response.json()['error'])

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

    def test_customer_login_nonexistent(self):
        response = self.client.post('/api/customer/login/',
            data=json.dumps({'email': 'nope@test.com', 'password': 'Test123!'}),
            content_type='application/json')
        self.assertEqual(response.status_code, 401)

    def test_logout(self):
        self.client.post('/api/customer/login/',
            data=json.dumps({'email': 'test@test.com', 'password': 'Test123!'}),
            content_type='application/json')
        response = self.client.post('/api/logout/', content_type='application/json')
        self.assertEqual(response.status_code, 200)


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

    def test_staff_register(self):
        response = self.client.post('/api/staff/register/',
            data=json.dumps({'userId': 'newstaff', 'email': 'newstaff@test.com', 'password': 'Staff123!'}),
            content_type='application/json')
        self.assertEqual(response.status_code, 201)


class ProductTests(TestCase):
    def setUp(self):
        self.client = Client()
        Product.objects.create(product_name='Test Milk', category='Dairy', unit_price=1.20, stock_quantity=10)
        Product.objects.create(product_name='Orange Juice', category='Beverages', unit_price=2.50, stock_quantity=20)
        Product.objects.create(product_name='Cheddar Cheese', category='Dairy', unit_price=3.00, stock_quantity=5)

    def test_product_list(self):
        response = self.client.get('/api/products/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['count'], 3)
        self.assertEqual(len(data['results']), 3)

    def test_product_search_by_name(self):
        response = self.client.get('/api/products/?search=milk')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['results'][0]['product_name'], 'Test Milk')

    def test_product_search_by_category(self):
        response = self.client.get('/api/products/?category=Dairy')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['count'], 2)

    def test_product_filter_category(self):
        response = self.client.get('/api/products/?category=Beverages')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['results'][0]['product_name'], 'Orange Juice')

    def test_product_search_no_results(self):
        response = self.client.get('/api/products/?search=nonexistent')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['count'], 0)

    def test_product_pagination(self):
        response = self.client.get('/api/products/?page=1&page_size=2')
        data = response.json()
        self.assertEqual(len(data['results']), 2)
        self.assertEqual(data['count'], 3)
        self.assertEqual(data['page'], 1)


class PublishProductTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.customer = Customer.objects.create(
            username='seller1',
            email='seller@test.com',
            password=make_password('Sell123!')
        )
        session = self.client.session
        session['customer_id'] = self.customer.id
        session['role'] = 'customer'
        session.save()

    def test_publish_product(self):
        response = self.client.post('/api/products/publish/',
            data=json.dumps({'productName': 'My Widget', 'unitPrice': 9.99, 'category': 'General'}),
            content_type='application/json')
        self.assertEqual(response.status_code, 201)
        p = Product.objects.get(product_name='My Widget')
        self.assertEqual(p.seller_id, self.customer.id)

    def test_publish_product_missing_name(self):
        response = self.client.post('/api/products/publish/',
            data=json.dumps({'unitPrice': 5.00}),
            content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_my_products(self):
        Product.objects.create(product_name='A', unit_price=1, seller=self.customer)
        Product.objects.create(product_name='B', unit_price=2, seller=self.customer)
        response = self.client.get('/api/products/my/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 2)

    def test_update_product(self):
        p = Product.objects.create(product_name='Old', unit_price=1, seller=self.customer)
        response = self.client.patch(f'/api/products/{p.id}/',
            data=json.dumps({'productName': 'New Name', 'unitPrice': 2.50}),
            content_type='application/json')
        self.assertEqual(response.status_code, 200)
        p.refresh_from_db()
        self.assertEqual(p.product_name, 'New Name')

    def test_delete_product(self):
        p = Product.objects.create(product_name='ToDelete', unit_price=1, seller=self.customer)
        response = self.client.delete(f'/api/products/{p.id}/delete/')
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Product.objects.filter(id=p.id).exists())

    def test_cannot_edit_others_product(self):
        other = Customer.objects.create(username='other', email='other@t.com', password=make_password('Other123!'))
        p = Product.objects.create(product_name='NotMine', unit_price=1, seller=other)
        response = self.client.patch(f'/api/products/{p.id}/',
            data=json.dumps({'productName': 'Hack'}),
            content_type='application/json')
        self.assertEqual(response.status_code, 404)

    def test_publish_unauthenticated(self):
        client = Client()
        response = client.post('/api/products/publish/',
            data=json.dumps({'productName': 'X', 'unitPrice': 1}),
            content_type='application/json')
        self.assertEqual(response.status_code, 401)


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

    def test_place_order_empty(self):
        response = self.client.post('/api/orders/',
            data=json.dumps({'items': []}),
            content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_place_order_unauthenticated(self):
        client = Client()
        response = client.post('/api/orders/',
            data=json.dumps({'items': [{'productId': self.product.id, 'qty': 1}]}),
            content_type='application/json')
        self.assertEqual(response.status_code, 401)

    def test_my_orders(self):
        response = self.client.get('/api/orders/my/')
        self.assertEqual(response.status_code, 200)

    def test_my_orders_unauthenticated(self):
        client = Client()
        response = client.get('/api/orders/my/')
        self.assertEqual(response.status_code, 401)


class RefundTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.customer = Customer.objects.create(
            username='refunduser', email='refund@test.com',
            password=make_password('Refund123!'))
        self.product = Product.objects.create(
            product_name='Refundable', unit_price=10.00, stock_quantity=5)
        self.order = Order.objects.create(
            customer=self.customer, total_amount=20.00, status='completed')
        self.item = OrderItem.objects.create(
            order=self.order, product=self.product, quantity=2)
        session = self.client.session
        session['customer_id'] = self.customer.id
        session['role'] = 'customer'
        session.save()

    def test_create_refund(self):
        response = self.client.post('/api/refunds/',
            data=json.dumps({'orderItemId': self.item.id, 'quantity': 1, 'reason': 'Defective'}),
            content_type='application/json')
        self.assertEqual(response.status_code, 201)

    def test_refund_non_completed_order(self):
        self.order.status = 'pending'
        self.order.save()
        response = self.client.post('/api/refunds/',
            data=json.dumps({'orderItemId': self.item.id, 'quantity': 1}),
            content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_refund_invalid_quantity(self):
        response = self.client.post('/api/refunds/',
            data=json.dumps({'orderItemId': self.item.id, 'quantity': 999}),
            content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_refund_duplicate_pending(self):
        RefundRequest.objects.create(
            customer=self.customer, order=self.order,
            order_item=self.item, quantity=1, status='pending')
        response = self.client.post('/api/refunds/',
            data=json.dumps({'orderItemId': self.item.id, 'quantity': 1}),
            content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_my_refunds(self):
        response = self.client.get('/api/refunds/my/')
        self.assertEqual(response.status_code, 200)

    def test_staff_process_refund(self):
        staff = Staff.objects.create(
            username='refstaff', email='refstaff@test.com',
            password=make_password('Staff123!'))
        refund = RefundRequest.objects.create(
            customer=self.customer, order=self.order,
            order_item=self.item, quantity=1, status='pending')
        staff_client = Client()
        session = staff_client.session
        session['staff_id'] = staff.id
        session['role'] = 'staff'
        session.save()
        response = staff_client.patch(f'/api/staff/refunds/{refund.id}/',
            data=json.dumps({'status': 'approved'}),
            content_type='application/json')
        self.assertEqual(response.status_code, 200)
        refund.refresh_from_db()
        self.assertEqual(refund.status, 'approved')


class StaffOrderTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.staff = Staff.objects.create(
            username='stafforder',
            email='stafforder@test.com',
            password=make_password('Staff123!')
        )
        self.customer = Customer.objects.create(
            username='cust1',
            email='cust1@test.com',
            password=make_password('Cust123!')
        )
        self.order = Order.objects.create(customer=self.customer, total_amount=10.00, status='pending')
        session = self.client.session
        session['staff_id'] = self.staff.id
        session['role'] = 'staff'
        session.save()

    def test_staff_view_orders(self):
        response = self.client.get('/api/staff/orders/')
        self.assertEqual(response.status_code, 200)

    def test_staff_update_order_status(self):
        response = self.client.patch(
            f'/api/staff/orders/{self.order.id}/',
            data=json.dumps({'status': 'processing'}),
            content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'processing')

    def test_staff_update_nonexistent_order(self):
        response = self.client.patch('/api/staff/orders/9999/',
            data=json.dumps({'status': 'completed'}),
            content_type='application/json')
        self.assertEqual(response.status_code, 404)


class InventoryTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.staff = Staff.objects.create(
            username='invstaff',
            email='inv@test.com',
            password=make_password('Staff123!')
        )
        self.product = Product.objects.create(
            product_name='Inv Product',
            category='Test',
            unit_price=5.00,
            stock_quantity=10
        )
        session = self.client.session
        session['staff_id'] = self.staff.id
        session['role'] = 'staff'
        session.save()

    def test_view_inventory(self):
        response = self.client.get('/api/staff/inventory/')
        self.assertEqual(response.status_code, 200)

    def test_stock_in(self):
        response = self.client.patch(
            f'/api/staff/inventory/{self.product.id}/',
            data=json.dumps({'mode': 'in', 'delta': 5}),
            content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 15)

    def test_stock_out(self):
        response = self.client.patch(
            f'/api/staff/inventory/{self.product.id}/',
            data=json.dumps({'mode': 'out', 'delta': 3}),
            content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 7)

    def test_stock_out_floor_zero(self):
        response = self.client.patch(
            f'/api/staff/inventory/{self.product.id}/',
            data=json.dumps({'mode': 'out', 'delta': 999}),
            content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 0)

    def test_inventory_unauthenticated(self):
        client = Client()
        response = client.get('/api/staff/inventory/')
        self.assertEqual(response.status_code, 401)

    def test_update_nonexistent_product(self):
        response = self.client.patch('/api/staff/inventory/9999/',
            data=json.dumps({'mode': 'in', 'delta': 1}),
            content_type='application/json')
        self.assertEqual(response.status_code, 404)


class FavoriteTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.customer = Customer.objects.create(
            username='favuser',
            email='fav@test.com',
            password=make_password('Fav12345')
        )
        self.product = Product.objects.create(
            product_name='Fav Product',
            category='Test',
            unit_price=1.50,
            stock_quantity=10
        )
        session = self.client.session
        session['customer_id'] = self.customer.id
        session['role'] = 'customer'
        session.save()

    def test_favorite_list_empty(self):
        response = self.client.get('/api/favorites/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 0)

    def test_favorite_toggle_add(self):
        response = self.client.post('/api/favorites/toggle/',
            data=json.dumps({'productId': self.product.id}),
            content_type='application/json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['status'], 'added')

    def test_favorite_toggle_remove(self):
        Favorite.objects.create(customer=self.customer, product=self.product)
        response = self.client.post('/api/favorites/toggle/',
            data=json.dumps({'productId': self.product.id}),
            content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'removed')

    def test_favorite_list_after_add(self):
        Favorite.objects.create(customer=self.customer, product=self.product)
        response = self.client.get('/api/favorites/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

    def test_favorite_toggle_nonexistent_product(self):
        response = self.client.post('/api/favorites/toggle/',
            data=json.dumps({'productId': 9999}),
            content_type='application/json')
        self.assertEqual(response.status_code, 404)

    def test_favorite_unauthenticated(self):
        client = Client()
        response = client.get('/api/favorites/')
        self.assertEqual(response.status_code, 401)


class ProfileTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.customer = Customer.objects.create(
            username='profuser', email='prof@test.com',
            password=make_password('Prof1234'), phone_number='000')
        session = self.client.session
        session['customer_id'] = self.customer.id
        session['role'] = 'customer'
        session.save()

    def test_get_profile(self):
        response = self.client.get('/api/customer/profile/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['username'], 'profuser')
        self.assertEqual(data['email'], 'prof@test.com')

    def test_update_email(self):
        response = self.client.patch('/api/customer/profile/',
            data=json.dumps({'email': 'new@prof.com'}),
            content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.email, 'new@prof.com')

    def test_update_password(self):
        response = self.client.patch('/api/customer/profile/',
            data=json.dumps({'password': 'NewPass99'}),
            content_type='application/json')
        self.assertEqual(response.status_code, 200)

    def test_update_weak_password(self):
        response = self.client.patch('/api/customer/profile/',
            data=json.dumps({'password': 'short'}),
            content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_profile_unauthenticated(self):
        client = Client()
        response = client.get('/api/customer/profile/')
        self.assertEqual(response.status_code, 401)


class ViewPageTests(TestCase):
    """Test that page views return correct status or redirect."""

    def setUp(self):
        self.client = Client()
        self.customer = Customer.objects.create(
            username='pageuser',
            email='page@test.com',
            password=make_password('Page123!')
        )
        self.staff = Staff.objects.create(
            username='pagestaff',
            email='pagestaff@test.com',
            password=make_password('Staff123!')
        )

    def test_home_shows_landing_when_not_logged_in(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'market/landing.html')

    def test_home_accessible_when_logged_in(self):
        session = self.client.session
        session['customer_id'] = self.customer.id
        session['role'] = 'customer'
        session['customer_username'] = self.customer.username
        session.save()
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_staff_dashboard_redirects_when_not_logged_in(self):
        response = self.client.get('/staff/dashboard/')
        self.assertEqual(response.status_code, 302)

    def test_products_page_redirects_when_not_logged_in(self):
        response = self.client.get('/products/')
        self.assertEqual(response.status_code, 302)

    def test_profile_redirects_when_not_logged_in(self):
        response = self.client.get('/profile/')
        self.assertEqual(response.status_code, 302)

    def test_customer_login_page(self):
        response = self.client.get('/login/')
        self.assertEqual(response.status_code, 200)

    def test_customer_register_page(self):
        response = self.client.get('/register/')
        self.assertEqual(response.status_code, 200)

    def test_staff_login_page(self):
        response = self.client.get('/staff/login/')
        self.assertEqual(response.status_code, 200)

    def test_forgot_password_page(self):
        response = self.client.get('/forgot-password/')
        self.assertEqual(response.status_code, 200)

    def test_reset_password_page_no_token(self):
        response = self.client.get('/reset-password/')
        self.assertEqual(response.status_code, 302)  # redirects to login


# ── Email Verification Tests ──────────────────────────────────

class EmailVerificationTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_register_sets_unverified(self):
        response = self.client.post('/api/customer/register/',
            data=json.dumps({'userId': 'vuser', 'email': 'v@test.com', 'password': 'Pass123!'}),
            content_type='application/json')
        self.assertEqual(response.status_code, 201)
        customer = Customer.objects.get(username='vuser')
        self.assertFalse(customer.is_verified)
        self.assertTrue(len(customer.verification_token) > 0)

    def test_register_sends_verification_email(self):
        self.client.post('/api/customer/register/',
            data=json.dumps({'userId': 'emailuser', 'email': 'email@test.com', 'password': 'Pass123!'}),
            content_type='application/json')
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Verify', mail.outbox[0].subject)
        self.assertIn('email@test.com', mail.outbox[0].to)

    def test_verify_valid_token(self):
        customer = Customer.objects.create(
            username='unverified', email='unv@test.com',
            password=make_password('Pass123!'),
            is_verified=False, verification_token='valid-token-123')
        response = self.client.get('/api/verify/?token=valid-token-123')
        self.assertEqual(response.status_code, 200)
        customer.refresh_from_db()
        self.assertTrue(customer.is_verified)
        self.assertEqual(customer.verification_token, '')

    def test_verify_invalid_token(self):
        response = self.client.get('/api/verify/?token=bad-token')
        self.assertEqual(response.status_code, 400)

    def test_verify_missing_token(self):
        response = self.client.get('/api/verify/')
        self.assertEqual(response.status_code, 400)

    def test_login_blocked_when_unverified(self):
        Customer.objects.create(
            username='blocked', email='blocked@test.com',
            password=make_password('Pass123!'),
            is_verified=False)
        response = self.client.post('/api/customer/login/',
            data=json.dumps({'email': 'blocked@test.com', 'password': 'Pass123!'}),
            content_type='application/json')
        self.assertEqual(response.status_code, 403)

    def test_view_verify_email_redirect(self):
        customer = Customer.objects.create(
            username='viewverify', email='vv@test.com',
            password=make_password('Pass123!'),
            is_verified=False, verification_token='view-token-abc')
        response = self.client.get('/verify/?token=view-token-abc')
        self.assertEqual(response.status_code, 302)  # redirects to login
        customer.refresh_from_db()
        self.assertTrue(customer.is_verified)


# ── Forgot Password Tests ────────────────────────────────────

class ForgotPasswordTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.customer = Customer.objects.create(
            username='forgotuser', email='forgot@test.com',
            password=make_password('Old123!!'),
            is_verified=True)

    def test_forgot_password_valid_email(self):
        response = self.client.post('/api/forgot-password/',
            data=json.dumps({'email': 'forgot@test.com'}),
            content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.customer.refresh_from_db()
        self.assertTrue(len(self.customer.password_reset_token) > 0)
        self.assertIsNotNone(self.customer.password_reset_expires)

    def test_forgot_password_unknown_email(self):
        response = self.client.post('/api/forgot-password/',
            data=json.dumps({'email': 'unknown@test.com'}),
            content_type='application/json')
        self.assertEqual(response.status_code, 200)  # no enumeration

    def test_forgot_password_sends_email(self):
        self.client.post('/api/forgot-password/',
            data=json.dumps({'email': 'forgot@test.com'}),
            content_type='application/json')
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Reset', mail.outbox[0].subject)

    def test_reset_password_valid_token(self):
        self.customer.password_reset_token = 'reset-token-xyz'
        self.customer.password_reset_expires = timezone.now() + timedelta(hours=1)
        self.customer.save()
        response = self.client.post('/api/reset-password/',
            data=json.dumps({'token': 'reset-token-xyz', 'password': 'NewPass99'}),
            content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.customer.refresh_from_db()
        self.assertTrue(check_password('NewPass99', self.customer.password))
        self.assertEqual(self.customer.password_reset_token, '')

    def test_reset_password_invalid_token(self):
        response = self.client.post('/api/reset-password/',
            data=json.dumps({'token': 'bad-token', 'password': 'NewPass99'}),
            content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_reset_password_expired_token(self):
        self.customer.password_reset_token = 'expired-tok'
        self.customer.password_reset_expires = timezone.now() - timedelta(hours=2)
        self.customer.save()
        response = self.client.post('/api/reset-password/',
            data=json.dumps({'token': 'expired-tok', 'password': 'NewPass99'}),
            content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_reset_password_weak_password(self):
        self.customer.password_reset_token = 'weak-tok'
        self.customer.password_reset_expires = timezone.now() + timedelta(hours=1)
        self.customer.save()
        response = self.client.post('/api/reset-password/',
            data=json.dumps({'token': 'weak-tok', 'password': 'short'}),
            content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_reset_password_missing_fields(self):
        response = self.client.post('/api/reset-password/',
            data=json.dumps({}),
            content_type='application/json')
        self.assertEqual(response.status_code, 400)


# ── Chat Room Tests ──────────────────────────────────────────

class ChatRoomTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.customer = Customer.objects.create(
            username='chatuser', email='chat@test.com',
            password=make_password('Chat123!'), is_verified=True)
        self.seller = Customer.objects.create(
            username='chatseller', email='seller@chat.com',
            password=make_password('Sell123!'), is_verified=True)
        session = self.client.session
        session['customer_id'] = self.customer.id
        session['customer_username'] = self.customer.username
        session['role'] = 'customer'
        session.save()

    def test_chat_rooms_unauthenticated(self):
        client = Client()
        response = client.get('/api/chat/rooms/')
        self.assertEqual(response.status_code, 401)

    def test_chat_rooms_customer_has_support(self):
        response = self.client.get('/api/chat/rooms/')
        self.assertEqual(response.status_code, 200)
        rooms = response.json()
        room_names = [r['room_name'] for r in rooms]
        self.assertIn(f'support_c{self.customer.id}', room_names)

    def test_chat_rooms_with_messages(self):
        ChatMessage.objects.create(
            room_name=f'seller{self.seller.id}p99',
            sender=self.customer.username, message='hi')
        response = self.client.get('/api/chat/rooms/')
        rooms = response.json()
        room_names = [r['room_name'] for r in rooms]
        self.assertIn(f'seller{self.seller.id}p99', room_names)

    def test_delete_chat_room(self):
        room = f'seller{self.seller.id}p99'
        ChatMessage.objects.create(room_name=room, sender=self.customer.username, message='hi')
        response = self.client.delete(f'/api/chat/rooms/{room}/delete/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ChatMessage.objects.filter(room_name=room).count(), 0)

    def test_cannot_delete_support_room(self):
        room = f'support_c{self.customer.id}'
        ChatMessage.objects.create(room_name=room, sender=self.customer.username, message='help')
        response = self.client.delete(f'/api/chat/rooms/{room}/delete/')
        self.assertEqual(response.status_code, 400)


# ── Notification Tests ───────────────────────────────────────

class NotificationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.customer = Customer.objects.create(
            username='notifuser', email='notif@test.com',
            password=make_password('Notif123!'), is_verified=True)
        session = self.client.session
        session['customer_id'] = self.customer.id
        session['role'] = 'customer'
        session.save()

    def test_notification_list(self):
        Notification.objects.create(
            recipient_type='customer', recipient_id=self.customer.id,
            message='Test notification')
        response = self.client.get('/api/notifications/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

    def test_notification_list_unauthenticated(self):
        client = Client()
        response = client.get('/api/notifications/')
        self.assertEqual(response.status_code, 401)

    def test_notification_count(self):
        Notification.objects.create(
            recipient_type='customer', recipient_id=self.customer.id,
            message='Unread', is_read=False)
        Notification.objects.create(
            recipient_type='customer', recipient_id=self.customer.id,
            message='Read', is_read=True)
        response = self.client.get('/api/notifications/count/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['count'], 1)

    def test_notification_mark_read(self):
        notif = Notification.objects.create(
            recipient_type='customer', recipient_id=self.customer.id,
            message='Mark me', is_read=False)
        response = self.client.patch(f'/api/notifications/{notif.id}/read/',
            content_type='application/json')
        self.assertEqual(response.status_code, 200)
        notif.refresh_from_db()
        self.assertTrue(notif.is_read)

    def test_notification_mark_read_wrong_user(self):
        other = Customer.objects.create(
            username='other_notif', email='other_n@test.com',
            password=make_password('Other123!'))
        notif = Notification.objects.create(
            recipient_type='customer', recipient_id=other.id,
            message='Not yours')
        response = self.client.patch(f'/api/notifications/{notif.id}/read/',
            content_type='application/json')
        self.assertEqual(response.status_code, 404)


# ── Confirm Receipt Tests ────────────────────────────────────

class ConfirmReceiptTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.customer = Customer.objects.create(
            username='confirmuser', email='confirm@test.com',
            password=make_password('Conf123!'), is_verified=True)
        self.seller = Customer.objects.create(
            username='confirmseller', email='cseller@test.com',
            password=make_password('Sell123!'), is_verified=True)
        self.product = Product.objects.create(
            product_name='Confirm Product', unit_price=5.00,
            stock_quantity=10, seller=self.seller)
        self.order = Order.objects.create(
            customer=self.customer, total_amount=10.00, status='pending')
        OrderItem.objects.create(
            order=self.order, product=self.product, quantity=2,
            product_name_snapshot='Confirm Product',
            unit_price_snapshot=5.00, seller_name_snapshot='confirmseller')
        session = self.client.session
        session['customer_id'] = self.customer.id
        session['role'] = 'customer'
        session.save()

    def test_confirm_pending_order(self):
        response = self.client.patch(f'/api/orders/{self.order.id}/confirm/',
            content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'completed')

    def test_confirm_non_pending_order(self):
        self.order.status = 'completed'
        self.order.save()
        response = self.client.patch(f'/api/orders/{self.order.id}/confirm/',
            content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_confirm_other_users_order(self):
        other = Customer.objects.create(
            username='otherconfirm', email='oc@test.com',
            password=make_password('Other123!'))
        other_order = Order.objects.create(
            customer=other, total_amount=5.00, status='pending')
        response = self.client.patch(f'/api/orders/{other_order.id}/confirm/',
            content_type='application/json')
        self.assertEqual(response.status_code, 404)

    def test_confirm_unauthenticated(self):
        client = Client()
        response = client.patch(f'/api/orders/{self.order.id}/confirm/',
            content_type='application/json')
        self.assertEqual(response.status_code, 401)


# ── Staff Product Delist Tests ───────────────────────────────

class StaffProductTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.staff = Staff.objects.create(
            username='deliststaff', email='delist@test.com',
            password=make_password('Staff123!'))
        self.seller = Customer.objects.create(
            username='delistseller', email='ds@test.com',
            password=make_password('Sell123!'))
        self.product = Product.objects.create(
            product_name='Delist Me', unit_price=10.00,
            stock_quantity=5, seller=self.seller, is_active=True)
        session = self.client.session
        session['staff_id'] = self.staff.id
        session['role'] = 'staff'
        session.save()

    def test_toggle_active_delist(self):
        response = self.client.patch(
            f'/api/staff/inventory/{self.product.id}/toggle-active/',
            content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.product.refresh_from_db()
        self.assertFalse(self.product.is_active)

    def test_toggle_active_relist(self):
        self.product.is_active = False
        self.product.save()
        response = self.client.patch(
            f'/api/staff/inventory/{self.product.id}/toggle-active/',
            content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.product.refresh_from_db()
        self.assertTrue(self.product.is_active)

    def test_toggle_active_unauthenticated(self):
        client = Client()
        response = client.patch(
            f'/api/staff/inventory/{self.product.id}/toggle-active/',
            content_type='application/json')
        self.assertEqual(response.status_code, 401)


# ── Order Snapshot Tests ─────────────────────────────────────

class OrderSnapshotTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.customer = Customer.objects.create(
            username='snapuser', email='snap@test.com',
            password=make_password('Snap123!'), is_verified=True)
        self.seller = Customer.objects.create(
            username='snapseller', email='snaps@test.com',
            password=make_password('Sell123!'))
        self.product = Product.objects.create(
            product_name='Snapshot Product', unit_price=15.00,
            stock_quantity=10, seller=self.seller)
        session = self.client.session
        session['customer_id'] = self.customer.id
        session['role'] = 'customer'
        session.save()

    def test_order_preserves_snapshots(self):
        # Place order
        response = self.client.post('/api/orders/',
            data=json.dumps({'items': [{'productId': self.product.id, 'qty': 1}]}),
            content_type='application/json')
        self.assertEqual(response.status_code, 201)
        item = OrderItem.objects.first()
        self.assertEqual(item.product_name_snapshot, 'Snapshot Product')
        self.assertEqual(item.unit_price_snapshot, 15.00)
        self.assertEqual(item.seller_name_snapshot, 'snapseller')

    def test_cannot_delete_product_with_orders(self):
        # Place an order first
        self.client.post('/api/orders/',
            data=json.dumps({'items': [{'productId': self.product.id, 'qty': 1}]}),
            content_type='application/json')
        # Switch to seller session
        seller_client = Client()
        session = seller_client.session
        session['customer_id'] = self.seller.id
        session['role'] = 'customer'
        session.save()
        response = seller_client.delete(f'/api/products/{self.product.id}/delete/')
        self.assertEqual(response.status_code, 400)


# ── Rate Limit Tests ─────────────────────────────────────────

class RateLimitTests(TestCase):
    def setUp(self):
        from django.core.cache import cache
        cache.clear()
        self.client = Client()
        self.customer = Customer.objects.create(
            username='rateuser', email='rate@test.com',
            password=make_password('Rate123!'),
            is_verified=True)

    def test_lockout_after_max_attempts(self):
        for _ in range(5):
            self.client.post('/api/customer/login/',
                data=json.dumps({'email': 'rate@test.com', 'password': 'wrong'}),
                content_type='application/json')
        response = self.client.post('/api/customer/login/',
            data=json.dumps({'email': 'rate@test.com', 'password': 'wrong'}),
            content_type='application/json')
        self.assertEqual(response.status_code, 429)

    def test_successful_login_clears_lockout(self):
        # Make 3 failed attempts
        for _ in range(3):
            self.client.post('/api/customer/login/',
                data=json.dumps({'email': 'rate@test.com', 'password': 'wrong'}),
                content_type='application/json')
        # Successful login should clear the counter
        response = self.client.post('/api/customer/login/',
            data=json.dumps({'email': 'rate@test.com', 'password': 'Rate123!'}),
            content_type='application/json')
        self.assertEqual(response.status_code, 200)
        # Should be able to fail again without being locked out
        response = self.client.post('/api/customer/login/',
            data=json.dumps({'email': 'rate@test.com', 'password': 'wrong'}),
            content_type='application/json')
        self.assertEqual(response.status_code, 401)  # not 429


# ── Edge Case Tests ──────────────────────────────────────────

class EdgeCaseTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.customer = Customer.objects.create(
            username='edgeuser', email='edge@test.com',
            password=make_password('Edge123!'), is_verified=True)
        session = self.client.session
        session['customer_id'] = self.customer.id
        session['role'] = 'customer'
        session.save()

    def test_register_duplicate_username(self):
        response = self.client.post('/api/customer/register/',
            data=json.dumps({'userId': 'edgeuser', 'email': 'new@edge.com', 'password': 'Pass123!'}),
            content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('Username', response.json()['error'])

    def test_publish_product_negative_price(self):
        response = self.client.post('/api/products/publish/',
            data=json.dumps({'productName': 'Bad Price', 'unitPrice': -5}),
            content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_publish_product_excessive_price(self):
        response = self.client.post('/api/products/publish/',
            data=json.dumps({'productName': 'Too Expensive', 'unitPrice': 9999999}),
            content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_favorite_toggle_missing_product_id(self):
        response = self.client.post('/api/favorites/toggle/',
            data=json.dumps({}),
            content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_staff_refund_list(self):
        staff = Staff.objects.create(
            username='edgestaff', email='edgestaff@test.com',
            password=make_password('Staff123!'))
        staff_client = Client()
        session = staff_client.session
        session['staff_id'] = staff.id
        session['role'] = 'staff'
        session.save()
        response = staff_client.get('/api/staff/refunds/')
        self.assertEqual(response.status_code, 200)

    def test_staff_register_duplicate_email(self):
        Staff.objects.create(
            username='dupstaff', email='dup@staff.com',
            password=make_password('Staff123!'))
        response = self.client.post('/api/staff/register/',
            data=json.dumps({'userId': 'dupstaff2', 'email': 'dup@staff.com', 'password': 'Staff123!'}),
            content_type='application/json')
        self.assertEqual(response.status_code, 400)
