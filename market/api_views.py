import re
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.hashers import make_password, check_password
from django.core.cache import cache
from .models import Customer, Staff, Product, Order, OrderItem, Favorite, RefundRequest, Notification, Category, ChatMessage
from .serializers import (CustomerSerializer, StaffSerializer, ProductSerializer,
                          OrderSerializer, FavoriteSerializer, RefundRequestSerializer,
                          NotificationSerializer, CategorySerializer)
from django.core.mail import send_mail
from django.db.models import Q, F, Sum, Count
from django.db import transaction
from decimal import Decimal
import secrets

# ── Password & rate-limit helpers ──────────────────────────
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_SECONDS = 300  # 5 minutes


def validate_password(password):
    """Enforce minimum password complexity."""
    if len(password) < 8:
        return 'Password must be at least 8 characters.'
    if not re.search(r'[A-Za-z]', password):
        return 'Password must contain at least one letter.'
    if not re.search(r'[0-9]', password):
        return 'Password must contain at least one digit.'
    return None


def check_rate_limit(email):
    """Return error message if too many failed login attempts."""
    key = f'login_fail_{email}'
    attempts = cache.get(key, 0)
    if attempts >= MAX_LOGIN_ATTEMPTS:
        return 'Too many failed attempts. Please try again in 5 minutes.'
    return None


def record_failed_login(email):
    key = f'login_fail_{email}'
    attempts = cache.get(key, 0)
    cache.set(key, attempts + 1, LOCKOUT_SECONDS)


def clear_failed_login(email):
    cache.delete(f'login_fail_{email}')


def create_notification(recipient_type, recipient_id, message, link=''):
    """Create a notification for a customer or staff member."""
    Notification.objects.create(
        recipient_type=recipient_type,
        recipient_id=recipient_id,
        message=message,
        link=link,
    )


@api_view(['POST'])
def customer_register(request):
    username = request.data.get('userId')
    email = request.data.get('email')
    password = request.data.get('password')

    if not username or not email or not password:
        return Response({'error': 'All fields are required.'}, status=400)
    pw_err = validate_password(password)
    if pw_err:
        return Response({'error': pw_err}, status=400)
    if Customer.objects.filter(username=username).exists():
        return Response({'error': 'Username already exists.'}, status=400)
    if Customer.objects.filter(email=email).exists():
        return Response({'error': 'Email already exists.'}, status=400)

    customer = Customer.objects.create(
        username=username,
        email=email,
        password=make_password(password),
        is_verified=True,
    )
    return Response({'message': 'Account created successfully.', 'userId': customer.username}, status=201)

@api_view(['POST'])
def customer_login(request):
    email = request.data.get('email', '')
    password = request.data.get('password', '')

    rate_err = check_rate_limit(email)
    if rate_err:
        return Response({'error': rate_err}, status=429)

    try:
        customer = Customer.objects.get(email=email)
        if check_password(password, customer.password):
            if not customer.is_verified:
                return Response({'error': 'Please verify your email before logging in.'}, status=403)
            clear_failed_login(email)
            request.session['customer_id'] = customer.id
            request.session['customer_username'] = customer.username
            request.session['role'] = 'customer'
            return Response({'message': 'Login successful.', 'userId': customer.username, 'role': 'customer'})
        record_failed_login(email)
        return Response({'error': 'Invalid credentials.'}, status=401)
    except Customer.DoesNotExist:
        record_failed_login(email)
        return Response({'error': 'Invalid credentials.'}, status=401)

@api_view(['POST'])
def staff_register(request):
    # Only allow staff registration from localhost
    remote = request.META.get('REMOTE_ADDR', '')
    if remote not in ('127.0.0.1', '::1', 'localhost'):
        return Response({'error': 'Staff registration is only available on the local server.'}, status=403)

    username = request.data.get('userId')
    email = request.data.get('email')
    password = request.data.get('password')

    if not username or not email or not password:
        return Response({'error': 'All fields are required.'}, status=400)
    pw_err = validate_password(password)
    if pw_err:
        return Response({'error': pw_err}, status=400)
    if Staff.objects.filter(username=username).exists():
        return Response({'error': 'Username already exists.'}, status=400)
    if Staff.objects.filter(email=email).exists():
        return Response({'error': 'Email already exists.'}, status=400)

    staff = Staff.objects.create(
        username=username,
        email=email,
        password=make_password(password)
    )
    return Response({'message': 'Staff account created successfully.', 'userId': staff.username}, status=201)

@api_view(['POST'])
def staff_login(request):
    email = request.data.get('email', '')
    password = request.data.get('password', '')

    rate_err = check_rate_limit(email)
    if rate_err:
        return Response({'error': rate_err}, status=429)

    try:
        staff = Staff.objects.get(email=email)
        if check_password(password, staff.password):
            clear_failed_login(email)
            request.session['staff_id'] = staff.id
            request.session['role'] = 'staff'
            return Response({'message': 'Login successful.', 'userId': staff.username, 'role': 'staff'})
        record_failed_login(email)
        return Response({'error': 'Invalid credentials.'}, status=401)
    except Staff.DoesNotExist:
        record_failed_login(email)
        return Response({'error': 'Invalid credentials.'}, status=401)

@api_view(['POST'])
def logout(request):
    request.session.flush()
    return Response({'message': 'Logged out successfully.'})


@api_view(['GET', 'PATCH'])
def customer_profile(request):
    customer_id = request.session.get('customer_id')
    if not customer_id:
        return Response({'error': 'Not authenticated.'}, status=401)
    try:
        customer = Customer.objects.get(id=customer_id)
    except Customer.DoesNotExist:
        return Response({'error': 'Customer not found.'}, status=404)

    if request.method == 'GET':
        return Response({
            'id': customer.id,
            'username': customer.username,
            'email': customer.email,
            'phone_number': customer.phone_number,
        })

    # PATCH — update profile fields
    if 'email' in request.data:
        new_email = request.data['email'].strip()
        if Customer.objects.filter(email=new_email).exclude(id=customer_id).exists():
            return Response({'error': 'Email already in use.'}, status=400)
        customer.email = new_email
    if 'phone_number' in request.data:
        customer.phone_number = request.data['phone_number'].strip()
    if 'password' in request.data:
        pw_err = validate_password(request.data['password'])
        if pw_err:
            return Response({'error': pw_err}, status=400)
        customer.password = make_password(request.data['password'])
    customer.save()
    return Response({'message': 'Profile updated.'})


@api_view(['GET'])
def product_list(request):
    products = Product.objects.select_related('seller').filter(is_active=True)
    # Search by product name (M3)
    search = request.GET.get('search', '').strip()
    if search:
        products = products.filter(product_name__icontains=search)
    category = request.GET.get('category', '').strip()
    if category:
        products = products.filter(category__iexact=category)

    # Pagination: ?page=1&page_size=20
    page = int(request.GET.get('page', 1))
    page_size = min(int(request.GET.get('page_size', 50)), 100)
    total = products.count()
    start = (page - 1) * page_size
    products = products[start:start + page_size]
    serializer = ProductSerializer(products, many=True, context={'request': request})
    return Response({
        'results': serializer.data,
        'count': total,
        'page': page,
        'page_size': page_size,
    })

@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def publish_product(request):
    customer_id = request.session.get('customer_id')
    if not customer_id:
        return Response({'error': 'Not authenticated.'}, status=401)

    name = request.data.get('productName', '').strip()
    category = request.data.get('category', 'General').strip()
    price = request.data.get('unitPrice')
    stock = int(request.data.get('stockQuantity', 1))
    description = request.data.get('description', '').strip()

    if not name or not price:
        return Response({'error': 'Product name and price are required.'}, status=400)

    try:
        price_decimal = Decimal(str(price))
    except Exception:
        return Response({'error': 'Invalid price value.'}, status=400)
    if price_decimal <= 0:
        return Response({'error': 'Price must be greater than zero.'}, status=400)
    if price_decimal > Decimal('999999.99'):
        return Response({'error': 'Price cannot exceed £999,999.99.'}, status=400)

    image = request.FILES.get('image')
    product = Product(
        product_name=name,
        category=category or 'General',
        unit_price=price_decimal,
        stock_quantity=max(1, stock),
        seller_id=customer_id,
        description=description,
    )
    if image:
        product.image = image
    product.save()
    return Response({'message': 'Product published successfully.', 'productId': product.id}, status=201)


@api_view(['GET'])
def my_products(request):
    customer_id = request.session.get('customer_id')
    if not customer_id:
        return Response({'error': 'Not authenticated.'}, status=401)
    products = Product.objects.filter(seller_id=customer_id).order_by('-id')
    serializer = ProductSerializer(products, many=True, context={'request': request})
    data = serializer.data
    # Check which products have been sold (exist in completed orders)
    sold_product_ids = set(
        OrderItem.objects.filter(
            product__seller_id=customer_id,
            order__status='completed'
        ).values_list('product_id', flat=True)
    )
    # Check which products have ANY orders (for delete protection)
    ordered_product_ids = set(
        OrderItem.objects.filter(
            product__seller_id=customer_id
        ).values_list('product_id', flat=True)
    )
    for item in data:
        item['has_sold'] = item['id'] in sold_product_ids
        item['has_orders'] = item['id'] in ordered_product_ids
    return Response(data)


@api_view(['PATCH'])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def update_product(request, product_id):
    customer_id = request.session.get('customer_id')
    if not customer_id:
        return Response({'error': 'Not authenticated.'}, status=401)
    try:
        product = Product.objects.get(id=product_id, seller_id=customer_id)
    except Product.DoesNotExist:
        return Response({'error': 'Product not found or not yours.'}, status=404)

    # Prevent editing sold products
    if OrderItem.objects.filter(product=product, order__status='completed').exists():
        return Response({'error': 'Cannot edit a product that has been sold.'}, status=400)

    if 'productName' in request.data:
        product.product_name = request.data['productName'].strip()
    if 'category' in request.data:
        product.category = request.data['category'].strip()
    if 'unitPrice' in request.data:
        product.unit_price = Decimal(str(request.data['unitPrice']))
    if 'stockQuantity' in request.data:
        product.stock_quantity = max(0, int(request.data['stockQuantity']))
    if 'description' in request.data:
        product.description = request.data['description'].strip()
    if 'image' in request.FILES:
        product.image = request.FILES['image']
    product.save()
    return Response({'message': 'Product updated.'})


@api_view(['DELETE'])
def delete_product(request, product_id):
    customer_id = request.session.get('customer_id')
    if not customer_id:
        return Response({'error': 'Not authenticated.'}, status=401)
    try:
        product = Product.objects.get(id=product_id, seller_id=customer_id)
    except Product.DoesNotExist:
        return Response({'error': 'Product not found or not yours.'}, status=404)
    # Prevent deleting products that have any orders (to preserve order history)
    if OrderItem.objects.filter(product=product).exists():
        return Response({'error': 'Cannot delete a product that has been ordered. You can set stock to 0 instead.'}, status=400)
    product.delete()
    return Response({'message': 'Product deleted.'})


@api_view(['POST'])
def place_order(request):
    customer_id = request.session.get('customer_id')
    if not customer_id:
        return Response({'error': 'Not authenticated.'}, status=401)

    items = request.data.get('items', [])
    if not items:
        return Response({'error': 'No items in order.'}, status=400)

    customer = Customer.objects.get(id=customer_id)
    total = Decimal('0.00')

    try:
        with transaction.atomic():
            order = Order.objects.create(customer=customer, total_amount=0)
            for item in items:
                product = Product.objects.select_for_update().get(id=item['productId'])
                qty = item['qty']
                if product.stock_quantity < qty:
                    raise ValueError(f'Not enough stock for {product.product_name}.')
                product.stock_quantity -= qty
                product.save()
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    product_name_snapshot=product.product_name,
                    unit_price_snapshot=product.unit_price,
                    seller_name_snapshot=product.seller.username if product.seller else 'Store',
                    quantity=qty,
                )
                total += product.unit_price * qty
            order.total_amount = total
            order.save()
    except ValueError as e:
        return Response({'error': str(e)}, status=400)

    return Response({'message': 'Order placed successfully.', 'orderId': order.id}, status=201)

@api_view(['GET'])
def my_orders(request):
    customer_id = request.session.get('customer_id')
    if not customer_id:
        return Response({'error': 'Not authenticated.'}, status=401)
    orders = Order.objects.filter(customer_id=customer_id).prefetch_related(
        'items__product__seller'
    ).order_by('-order_time')
    serializer = OrderSerializer(orders, many=True)
    return Response(serializer.data)


@api_view(['PATCH'])
def confirm_receipt(request, order_id):
    """Buyer confirms receipt of an order — changes status to completed."""
    customer_id = request.session.get('customer_id')
    if not customer_id:
        return Response({'error': 'Not authenticated.'}, status=401)
    try:
        order = Order.objects.get(id=order_id, customer_id=customer_id)
    except Order.DoesNotExist:
        return Response({'error': 'Order not found.'}, status=404)
    if order.status != 'pending':
        return Response({'error': 'Only pending orders can be confirmed.'}, status=400)
    order.status = 'completed'
    order.save()
    # Notify sellers about the confirmed receipt
    seller_ids = set()
    for item in order.items.select_related('product'):
        if item.product and item.product.seller_id:
            seller_ids.add(item.product.seller_id)
    for sid in seller_ids:
        create_notification(
            'customer', sid,
            f'Order #{order.id} has been confirmed as received by the buyer.',
            '/orders/'
        )
    return Response({'message': 'Order confirmed as received.', 'status': 'completed'})

@api_view(['GET'])
def staff_orders(request):
    if request.session.get('role') != 'staff':
        return Response({'error': 'Not authenticated.'}, status=401)
    orders = Order.objects.all().order_by('-order_time')
    serializer = OrderSerializer(orders, many=True)
    return Response(serializer.data)

@api_view(['PATCH'])
def update_order_status(request, order_id):
    if request.session.get('role') != 'staff':
        return Response({'error': 'Not authenticated.'}, status=401)
    try:
        order = Order.objects.get(id=order_id)
        new_status = request.data.get('status', order.status)
        order.status = new_status
        order.save()
        create_notification(
            'customer', order.customer_id,
            f'Your order #{order.id} status has been updated to {new_status}.',
            '/orders/'
        )
        return Response({'message': 'Order updated.'})
    except Order.DoesNotExist:
        return Response({'error': 'Order not found.'}, status=404)

@api_view(['GET'])
def inventory(request):
    if request.session.get('role') != 'staff':
        return Response({'error': 'Not authenticated.'}, status=401)
    products = Product.objects.all()
    serializer = ProductSerializer(products, many=True, context={'request': request})
    return Response(serializer.data)

@api_view(['PATCH'])
def update_inventory(request, product_id):
    if request.session.get('role') != 'staff':
        return Response({'error': 'Not authenticated.'}, status=401)
    try:
        product = Product.objects.get(id=product_id)
        mode = request.data.get('mode')
        delta = int(request.data.get('delta', 0))
        if mode == 'in':
            product.stock_quantity += delta
        elif mode == 'out':
            product.stock_quantity = max(0, product.stock_quantity - delta)
        product.save()
        return Response({'message': 'Stock updated.'})
    except Product.DoesNotExist:
        return Response({'error': 'Product not found.'}, status=404)


@api_view(['PATCH'])
def toggle_product_active(request, product_id):
    """Staff can delist (deactivate) or relist (reactivate) a product."""
    if request.session.get('role') != 'staff':
        return Response({'error': 'Not authenticated.'}, status=401)
    try:
        product = Product.objects.get(id=product_id)
        product.is_active = not product.is_active
        product.save()
        action = 'relisted' if product.is_active else 'delisted'
        # Notify the seller
        if product.seller_id:
            create_notification(
                'customer', product.seller_id,
                f'Your product "{product.product_name}" has been {action} by staff.',
                '/home/'
            )
        return Response({'message': f'Product {action}.', 'is_active': product.is_active})
    except Product.DoesNotExist:
        return Response({'error': 'Product not found.'}, status=404)


# ── Favorites (C1) ──────────────────────────────────────────────

@api_view(['GET'])
def favorite_list(request):
    customer_id = request.session.get('customer_id')
    if not customer_id:
        return Response({'error': 'Not authenticated.'}, status=401)
    favorites = Favorite.objects.filter(customer_id=customer_id).select_related('product')
    serializer = FavoriteSerializer(favorites, many=True)
    return Response(serializer.data)


@api_view(['POST'])
def favorite_toggle(request):
    customer_id = request.session.get('customer_id')
    if not customer_id:
        return Response({'error': 'Not authenticated.'}, status=401)
    product_id = request.data.get('productId')
    if not product_id:
        return Response({'error': 'productId is required.'}, status=400)
    try:
        Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        return Response({'error': 'Product not found.'}, status=404)

    fav, created = Favorite.objects.get_or_create(
        customer_id=customer_id, product_id=product_id
    )
    if not created:
        fav.delete()
        return Response({'status': 'removed'})
    return Response({'status': 'added'}, status=201)


# ── Refund Requests ────────────────────────────────────────────

@api_view(['POST'])
def create_refund(request):
    customer_id = request.session.get('customer_id')
    if not customer_id:
        return Response({'error': 'Not authenticated.'}, status=401)

    order_item_id = request.data.get('orderItemId')
    quantity = int(request.data.get('quantity', 1))
    reason = request.data.get('reason', '')

    try:
        order_item = OrderItem.objects.select_related('order').get(id=order_item_id)
    except OrderItem.DoesNotExist:
        return Response({'error': 'Order item not found.'}, status=404)

    order = order_item.order
    if order.customer_id != customer_id:
        return Response({'error': 'Not your order.'}, status=403)
    if order.status != 'completed':
        return Response({'error': 'Only completed orders can be refunded.'}, status=400)
    if quantity < 1 or quantity > order_item.quantity:
        return Response({'error': 'Invalid quantity.'}, status=400)
    if RefundRequest.objects.filter(order_item=order_item, status='pending').exists():
        return Response({'error': 'A pending refund already exists for this item.'}, status=400)

    refund = RefundRequest.objects.create(
        customer_id=customer_id,
        order=order,
        order_item=order_item,
        quantity=quantity,
        reason=reason,
    )
    return Response({'message': 'Refund request submitted.', 'refundId': refund.id}, status=201)


@api_view(['GET'])
def my_refunds(request):
    customer_id = request.session.get('customer_id')
    if not customer_id:
        return Response({'error': 'Not authenticated.'}, status=401)
    refunds = RefundRequest.objects.filter(customer_id=customer_id).select_related(
        'order_item__product', 'order'
    ).order_by('-created_time')
    serializer = RefundRequestSerializer(refunds, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def staff_refund_list(request):
    if request.session.get('role') != 'staff':
        return Response({'error': 'Not authenticated.'}, status=401)
    status_filter = request.GET.get('status', '')
    refunds = RefundRequest.objects.select_related(
        'customer', 'order_item__product', 'order'
    ).order_by('-created_time')
    if status_filter:
        refunds = refunds.filter(status=status_filter)
    serializer = RefundRequestSerializer(refunds, many=True)
    return Response(serializer.data)


@api_view(['PATCH'])
def process_refund(request, refund_id):
    staff_id = request.session.get('staff_id')
    if request.session.get('role') != 'staff':
        return Response({'error': 'Not authenticated.'}, status=401)
    try:
        refund = RefundRequest.objects.select_related('order_item__product', 'order').get(id=refund_id)
    except RefundRequest.DoesNotExist:
        return Response({'error': 'Refund not found.'}, status=404)

    new_status = request.data.get('status')
    if new_status not in ('approved', 'rejected'):
        return Response({'error': 'Status must be approved or rejected.'}, status=400)

    with transaction.atomic():
        refund.status = new_status
        refund.staff_id = staff_id
        refund.save()

        if new_status == 'approved':
            product = Product.objects.select_for_update().get(id=refund.order_item.product_id)
            product.stock_quantity += refund.quantity
            product.save()
            order = refund.order
            order.status = 'cancelled'
            order.save()

    # Create notification for customer
    create_notification(
        'customer', refund.customer_id,
        f'Your refund request #{refund.id} has been {new_status}.',
        '/refunds/'
    )

    return Response({'message': f'Refund {new_status}.'})


# ── Email Verification ────────────────────────────────────────

@api_view(['GET'])
def verify_email_api(request):
    token = request.GET.get('token', '')
    if not token:
        return Response({'error': 'Token is required.'}, status=400)
    try:
        customer = Customer.objects.get(verification_token=token)
        customer.is_verified = True
        customer.verification_token = ''
        customer.save()
        return Response({'message': 'Email verified successfully. You can now log in.'})
    except Customer.DoesNotExist:
        return Response({'error': 'Invalid or expired token.'}, status=400)


# ── Notifications ─────────────────────────────────────────────

@api_view(['GET'])
def notification_list(request):
    role = request.session.get('role')
    if role == 'customer':
        rid = request.session.get('customer_id')
    elif role == 'staff':
        rid = request.session.get('staff_id')
    else:
        return Response({'error': 'Not authenticated.'}, status=401)
    notifs = Notification.objects.filter(recipient_type=role, recipient_id=rid)[:50]
    serializer = NotificationSerializer(notifs, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def notification_count(request):
    role = request.session.get('role')
    if role == 'customer':
        rid = request.session.get('customer_id')
    elif role == 'staff':
        rid = request.session.get('staff_id')
    else:
        return Response({'error': 'Not authenticated.'}, status=401)
    count = Notification.objects.filter(recipient_type=role, recipient_id=rid, is_read=False).count()
    return Response({'count': count})


@api_view(['PATCH'])
def notification_mark_read(request, notif_id):
    role = request.session.get('role')
    if role == 'customer':
        rid = request.session.get('customer_id')
    elif role == 'staff':
        rid = request.session.get('staff_id')
    else:
        return Response({'error': 'Not authenticated.'}, status=401)
    try:
        notif = Notification.objects.get(id=notif_id, recipient_type=role, recipient_id=rid)
        notif.is_read = True
        notif.save()
        return Response({'message': 'Marked as read.'})
    except Notification.DoesNotExist:
        return Response({'error': 'Notification not found.'}, status=404)


# ── Seller Stats ──────────────────────────────────────────────

@api_view(['GET'])
def seller_stats(request):
    customer_id = request.session.get('customer_id')
    if not customer_id:
        return Response({'error': 'Not authenticated.'}, status=401)
    stats = OrderItem.objects.filter(
        product__seller_id=customer_id
    ).aggregate(
        total_revenue=Sum(F('quantity') * F('product__unit_price')),
        total_items_sold=Sum('quantity'),
        total_orders=Count('order', distinct=True),
    )
    return Response({
        'total_revenue': str(stats['total_revenue'] or 0),
        'total_items_sold': stats['total_items_sold'] or 0,
        'total_orders': stats['total_orders'] or 0,
    })


# ── Categories ────────────────────────────────────────────────

@api_view(['GET'])
def category_list(request):
    categories = Category.objects.all().order_by('name')
    serializer = CategorySerializer(categories, many=True)
    return Response(serializer.data)


# ── Chat Rooms ───────────────────────────────────────────────

def _parse_seller_room(room_name):
    """Parse room names like 'seller3p5' → (seller_id=3, product_id=5)
       or legacy 'seller3' → (seller_id=3, product_id=None)."""
    import re as _re
    m = _re.match(r'^seller(\d+)p(\d+)$', room_name)
    if m:
        return int(m.group(1)), int(m.group(2))
    m = _re.match(r'^seller(\d+)$', room_name)
    if m:
        return int(m.group(1)), None
    return None, None


@api_view(['GET'])
def chat_rooms(request):
    """Return list of chat rooms the current user has participated in."""
    role = request.session.get('role')
    if role == 'customer':
        username = request.session.get('customer_username', '')
        customer_id = request.session.get('customer_id')
        # Rooms where this customer sent messages
        sent_rooms = set(
            ChatMessage.objects.filter(sender=username)
            .values_list('room_name', flat=True)
        )
        # Also include rooms where this customer is the seller being contacted
        # Match both new format (seller{id}p{pid}) and legacy (seller{id})
        all_room_names = set(ChatMessage.objects.values_list('room_name', flat=True))
        for rn in all_room_names:
            sid, _ = _parse_seller_room(rn)
            if sid == customer_id:
                sent_rooms.add(rn)
        # Each customer has their own private support room
        my_support = f'support_c{customer_id}'
        sent_rooms.add(my_support)
        # Remove legacy shared 'support' room if present
        sent_rooms.discard('support')
        user_rooms = list(sent_rooms)
    elif role == 'staff':
        staff_username = request.session.get('staff_username', '')
        # Staff sees all support_c* rooms (individual customer support chats)
        # plus any other rooms staff has participated in
        staff_rooms = set(
            ChatMessage.objects.filter(sender=staff_username)
            .values_list('room_name', flat=True)
        )
        # Also include all support rooms that have messages (so staff can see pending requests)
        support_rooms = set(
            ChatMessage.objects.filter(room_name__startswith='support_c')
            .values_list('room_name', flat=True)
        )
        staff_rooms.update(support_rooms)
        # Remove legacy shared 'support' room
        staff_rooms.discard('support')
        user_rooms = list(staff_rooms)
    else:
        return Response({'error': 'Not authenticated.'}, status=401)

    # Build room info with last message and display name
    rooms = []
    for room_name in user_rooms:
        last_msg = ChatMessage.objects.filter(room_name=room_name).order_by('-timestamp').first()

        # Derive display name and product info from room name
        display_name = f'Room: {room_name}'
        product_info = None

        if room_name == 'support':
            display_name = 'Customer Support'
        elif room_name.startswith('support_c'):
            # Private support room: support_c{customer_id}
            import re as _re
            m = _re.match(r'^support_c(\d+)$', room_name)
            if m:
                cid = int(m.group(1))
                if role == 'staff':
                    # Staff sees customer name
                    try:
                        cust = Customer.objects.get(id=cid)
                        display_name = f'Support: {cust.username}'
                    except Customer.DoesNotExist:
                        display_name = f'Support: Customer #{cid}'
                else:
                    display_name = 'Customer Support'
            else:
                display_name = 'Customer Support'
        elif room_name.startswith('seller'):
            seller_id, product_id = _parse_seller_room(room_name)
            # Display seller name
            if seller_id:
                try:
                    seller = Customer.objects.get(id=seller_id)
                    display_name = f'Chat with {seller.username}'
                except Customer.DoesNotExist:
                    display_name = f'Room: {room_name}'

            # Get product info from room name (new format) or from messages (legacy)
            if product_id:
                try:
                    p = Product.objects.get(id=product_id)
                    product_info = {
                        'id': p.id,
                        'name': p.product_name,
                        'code': f'PROD-{p.id:05d}',
                        'image': request.build_absolute_uri(p.image.url) if p.image else '',
                    }
                except Product.DoesNotExist:
                    pass

        # Fallback: find product from messages if not already found
        if not product_info:
            product_msg = ChatMessage.objects.filter(
                room_name=room_name, product__isnull=False
            ).select_related('product').order_by('-timestamp').first()
            if product_msg and product_msg.product:
                p = product_msg.product
                product_info = {
                    'id': p.id,
                    'name': p.product_name,
                    'code': f'PROD-{p.id:05d}',
                    'image': request.build_absolute_uri(p.image.url) if p.image else '',
                }

        rooms.append({
            'room_name': room_name,
            'display_name': display_name,
            'last_message': last_msg.message[:60] if last_msg else '',
            'last_sender': last_msg.sender if last_msg else '',
            'last_time': last_msg.timestamp.isoformat() if last_msg else '',
            'product': product_info,
        })

    # Sort: rooms with recent messages first
    rooms.sort(key=lambda r: r['last_time'] or '', reverse=True)
    return Response(rooms)


@api_view(['DELETE'])
def delete_chat_room(request, room_name):
    """Delete all messages in a chat room (clear chat history)."""
    role = request.session.get('role')
    if role == 'customer':
        username = request.session.get('customer_username', '')
        customer_id = request.session.get('customer_id')
        # Customers can only delete rooms they participate in
        # Check: either they sent messages or they are the seller
        is_participant = ChatMessage.objects.filter(room_name=room_name, sender=username).exists()
        sid, _ = _parse_seller_room(room_name)
        is_seller = (sid == customer_id)
        if not is_participant and not is_seller:
            return Response({'error': 'Not your chat room.'}, status=403)
    elif role == 'staff':
        pass  # Staff can delete any room
    else:
        return Response({'error': 'Not authenticated.'}, status=401)

    # Cannot delete support rooms
    if room_name == 'support' or room_name.startswith('support_c'):
        return Response({'error': 'Cannot delete support chat rooms.'}, status=400)

    count, _ = ChatMessage.objects.filter(room_name=room_name).delete()
    return Response({'message': f'Chat room deleted ({count} messages removed).'})
