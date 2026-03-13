from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.hashers import make_password, check_password
from .models import Customer, Staff, Product, Order, OrderItem
from .serializers import CustomerSerializer, StaffSerializer, ProductSerializer, OrderSerializer
from decimal import Decimal

@api_view(['POST'])
def customer_register(request):
    username = request.data.get('userId')
    email = request.data.get('email')
    password = request.data.get('password')

    if not username or not email or not password:
        return Response({'error': 'All fields are required.'}, status=400)
    if Customer.objects.filter(username=username).exists():
        return Response({'error': 'Username already exists.'}, status=400)
    if Customer.objects.filter(email=email).exists():
        return Response({'error': 'Email already exists.'}, status=400)

    customer = Customer.objects.create(
        username=username,
        email=email,
        password=make_password(password)
    )
    return Response({'message': 'Account created successfully.', 'userId': customer.username}, status=201)

@api_view(['POST'])
def customer_login(request):
    email = request.data.get('email')
    password = request.data.get('password')

    try:
        customer = Customer.objects.get(email=email)
        if check_password(password, customer.password):
            request.session['customer_id'] = customer.id
            request.session['role'] = 'customer'
            return Response({'message': 'Login successful.', 'userId': customer.username, 'role': 'customer'})
        return Response({'error': 'Invalid credentials.'}, status=401)
    except Customer.DoesNotExist:
        return Response({'error': 'Invalid credentials.'}, status=401)

@api_view(['POST'])
def staff_register(request):
    username = request.data.get('userId')
    email = request.data.get('email')
    password = request.data.get('password')

    if not username or not email or not password:
        return Response({'error': 'All fields are required.'}, status=400)
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
    email = request.data.get('email')
    password = request.data.get('password')

    try:
        staff = Staff.objects.get(email=email)
        if check_password(password, staff.password):
            request.session['staff_id'] = staff.id
            request.session['role'] = 'staff'
            return Response({'message': 'Login successful.', 'userId': staff.username, 'role': 'staff'})
        return Response({'error': 'Invalid credentials.'}, status=401)
    except Staff.DoesNotExist:
        return Response({'error': 'Invalid credentials.'}, status=401)

@api_view(['POST'])
def logout(request):
    request.session.flush()
    return Response({'message': 'Logged out successfully.'})

@api_view(['GET'])
def product_list(request):
    products = Product.objects.all()
    serializer = ProductSerializer(products, many=True)
    return Response(serializer.data)

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

    order = Order.objects.create(customer=customer, total_amount=0)

    for item in items:
        product = Product.objects.get(id=item['productId'])
        qty = item['qty']
        if product.stock_quantity < qty:
            order.delete()
            return Response({'error': f'Not enough stock for {product.product_name}.'}, status=400)
        product.stock_quantity -= qty
        product.save()
        OrderItem.objects.create(order=order, product=product, quantity=qty)
        total += product.unit_price * qty

    order.total_amount = total
    order.save()
    return Response({'message': 'Order placed successfully.', 'orderId': order.id}, status=201)

@api_view(['GET'])
def my_orders(request):
    customer_id = request.session.get('customer_id')
    if not customer_id:
        return Response({'error': 'Not authenticated.'}, status=401)
    orders = Order.objects.filter(customer_id=customer_id).order_by('-order_time')
    serializer = OrderSerializer(orders, many=True)
    return Response(serializer.data)

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
        order.status = request.data.get('status', order.status)
        order.save()
        return Response({'message': 'Order updated.'})
    except Order.DoesNotExist:
        return Response({'error': 'Order not found.'}, status=404)

@api_view(['GET'])
def inventory(request):
    if request.session.get('role') != 'staff':
        return Response({'error': 'Not authenticated.'}, status=401)
    products = Product.objects.all()
    serializer = ProductSerializer(products, many=True)
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
