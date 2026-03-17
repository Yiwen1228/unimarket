import re
import secrets
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.hashers import make_password, check_password
from django.core.mail import send_mail
from .models import Customer, Staff, Product, ChatMessage


def _password_ok(password):
    if len(password) < 8:
        return 'Password must be at least 8 characters.'
    if not re.search(r'[A-Za-z]', password):
        return 'Password must contain at least one letter.'
    if not re.search(r'[0-9]', password):
        return 'Password must contain at least one digit.'
    return None


def customer_register(request):
    if request.method == 'POST':
        username = request.POST.get('username', '')
        email = request.POST.get('email', '')
        password = request.POST.get('password', '')
        if not username or not email or not password:
            messages.error(request, 'All fields are required.')
            return render(request, 'market/customer_register.html')
        pw_err = _password_ok(password)
        if pw_err:
            messages.error(request, pw_err)
            return render(request, 'market/customer_register.html')
        if Customer.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
        elif Customer.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists.')
        else:
            token = secrets.token_urlsafe(32)
            customer = Customer.objects.create(
                username=username,
                email=email,
                password=make_password(password),
                is_verified=False,
                verification_token=token,
            )
            from .utils import send_verification_email
            send_verification_email(customer, request)
            messages.success(request, 'Registration successful! Please check your email to verify your account.')
            return redirect('customer_login')
    return render(request, 'market/customer_register.html')


def customer_login(request):
    # TODO: add better error handling
    if request.method == 'POST':
        email = request.POST.get('email', '')
        password = request.POST.get('password', '')
        try:
            customer = Customer.objects.get(email=email)
            if check_password(password, customer.password):
                if not customer.is_verified:
                    messages.error(request, 'Please verify your email before logging in.')
                    return render(request, 'market/customer_login.html')
                request.session['customer_id'] = customer.id
                request.session['customer_username'] = customer.username
                request.session['role'] = 'customer'
                return redirect('home')
            else:
                messages.error(request, 'Invalid email or password.')
        except Customer.DoesNotExist:
            messages.error(request, 'Invalid email or password.')
    return render(request, 'market/customer_login.html')


def customer_logout(request):
    request.session.flush()
    return redirect('customer_login')


def staff_login(request):
    if request.method == 'POST':
        email = request.POST.get('email', '')
        password = request.POST.get('password', '')
        try:
            staff = Staff.objects.get(email=email)
            if check_password(password, staff.password):
                request.session['staff_id'] = staff.id
                request.session['staff_username'] = staff.username
                request.session['role'] = 'staff'
                return redirect('staff_dashboard')
            else:
                messages.error(request, 'Invalid email or password.')
        except Staff.DoesNotExist:
            messages.error(request, 'Invalid email or password.')
    return render(request, 'market/staff_login.html')


def staff_logout(request):
    request.session.flush()
    return redirect('staff_login')


def home(request):
    if 'customer_id' not in request.session:
        return render(request, 'market/landing.html')
    return render(request, 'market/home.html')


def profile(request):
    if 'customer_id' not in request.session:
        return redirect('customer_login')
    return render(request, 'market/profile.html')


def products(request):
    if 'customer_id' not in request.session:
        return redirect('customer_login')
    return render(request, 'market/products.html')


def my_orders(request):
    if 'customer_id' not in request.session:
        return redirect('customer_login')
    return render(request, 'market/my_orders.html')


def favorites(request):
    if 'customer_id' not in request.session:
        return redirect('customer_login')
    return render(request, 'market/favorites.html')


def chat(request):
    if 'customer_id' not in request.session:
        return redirect('customer_login')
    customer_id = request.session['customer_id']
    room = request.GET.get('room', 'support')
    # Each customer gets their own private support room
    if room == 'support':
        room = f'support_c{customer_id}'
    product_name = request.GET.get('product', '')
    product_id = request.GET.get('productId', '')
    context = {'chat_room': room, 'chat_product': product_name}

    # Look up product details if productId is provided
    if product_id:
        try:
            prod = Product.objects.get(id=int(product_id))
            context['chat_product'] = prod.product_name
            context['chat_product_id'] = prod.id
            context['chat_product_code'] = f'PROD-{prod.id:05d}'
            context['chat_product_image'] = prod.image.url if prod.image else ''
        except (Product.DoesNotExist, ValueError):
            pass

    return render(request, 'market/chat.html', context)


def staff_dashboard(request):
    if 'staff_id' not in request.session:
        return redirect('staff_login')
    return render(request, 'market/staff_dashboard.html')


def staff_orders(request):
    if 'staff_id' not in request.session:
        return redirect('staff_login')
    return render(request, 'market/staff_orders.html')


def staff_inventory(request):
    if 'staff_id' not in request.session:
        return redirect('staff_login')
    return render(request, 'market/staff_inventory.html')


def staff_chat(request):
    if 'staff_id' not in request.session:
        return redirect('staff_login')
    room = request.GET.get('room', '')
    # Default to first available support room or empty
    if not room or room == 'support':
        # Find the first support_c* room that exists, or just show empty state
        first_support = ChatMessage.objects.filter(
            room_name__startswith='support_c'
        ).values_list('room_name', flat=True).first()
        room = first_support or 'support_c0'
    staff_username = request.session.get('staff_username', '')
    # Staff can access support_c* rooms (customer support) and rooms they participated in
    if not room.startswith('support_c') and not ChatMessage.objects.filter(room_name=room, sender=staff_username).exists():
        return redirect('/staff/chat/')
    product_name = request.GET.get('product', '')
    product_id = request.GET.get('productId', '')
    context = {'chat_room': room, 'chat_product': product_name}

    if product_id:
        try:
            prod = Product.objects.get(id=int(product_id))
            context['chat_product'] = prod.product_name
            context['chat_product_id'] = prod.id
            context['chat_product_code'] = f'PROD-{prod.id:05d}'
            context['chat_product_image'] = prod.image.url if prod.image else ''
        except (Product.DoesNotExist, ValueError):
            pass

    return render(request, 'market/staff_chat.html', context)


def my_refunds_page(request):
    if 'customer_id' not in request.session:
        return redirect('customer_login')
    return render(request, 'market/my_refunds.html')


def staff_refunds_page(request):
    if 'staff_id' not in request.session:
        return redirect('staff_login')
    return render(request, 'market/staff_refunds.html')


def about_us(request):
    return render(request, 'market/about_us.html')


def contact(request):
    return render(request, 'market/contact.html')


def policy(request):
    return render(request, 'market/policy.html')


def verify_email(request):
    token = request.GET.get('token', '')
    if not token:
        messages.error(request, 'Invalid verification link.')
        return redirect('customer_login')
    try:
        customer = Customer.objects.get(verification_token=token)
        customer.is_verified = True
        customer.verification_token = ''
        customer.save()
        messages.success(request, 'Email verified successfully! You can now log in.')
    except Customer.DoesNotExist:
        messages.error(request, 'Invalid or expired verification link.')
    return redirect('customer_login')


def forgot_password_page(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        if email:
            try:
                customer = Customer.objects.get(email=email)
                token = secrets.token_urlsafe(32)
                customer.password_reset_token = token
                from django.utils import timezone
                from datetime import timedelta
                customer.password_reset_expires = timezone.now() + timedelta(hours=1)
                customer.save()
                from .utils import send_password_reset_email
                send_password_reset_email(customer, request)
            except Customer.DoesNotExist:
                pass  # Don't reveal whether the email exists
        messages.success(request, 'If that email is registered, a reset link has been sent.')
        return redirect('customer_login')
    return render(request, 'market/forgot_password.html')


def reset_password_page(request):
    token = request.GET.get('token', '') or request.POST.get('token', '')
    if request.method == 'POST':
        password = request.POST.get('password', '')
        confirm = request.POST.get('confirm_password', '')
        if password != confirm:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'market/reset_password.html', {'token': token})
        pw_err = _password_ok(password)
        if pw_err:
            messages.error(request, pw_err)
            return render(request, 'market/reset_password.html', {'token': token})
        try:
            customer = Customer.objects.get(password_reset_token=token)
        except Customer.DoesNotExist:
            messages.error(request, 'Invalid or expired reset link.')
            return redirect('customer_login')
        from django.utils import timezone
        if not customer.password_reset_expires or customer.password_reset_expires < timezone.now():
            messages.error(request, 'This reset link has expired.')
            return redirect('customer_login')
        customer.password = make_password(password)
        customer.password_reset_token = ''
        customer.password_reset_expires = None
        customer.save()
        messages.success(request, 'Password reset successfully. You can now log in.')
        return redirect('customer_login')
    # GET
    if not token:
        messages.error(request, 'Invalid reset link.')
        return redirect('customer_login')
    return render(request, 'market/reset_password.html', {'token': token})
