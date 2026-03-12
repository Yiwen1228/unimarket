from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Customer, Staff


def customer_register(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        phone = request.POST['phone_number']
        if Customer.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists')
        else:
            Customer.objects.create(username=username, password=password, phone_number=phone)
            messages.success(request, 'Registration successful, please login')
            return redirect('customer_login')
    return render(request, 'market/customer_login.html')


def customer_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        try:
            customer = Customer.objects.get(username=username, password=password)
            request.session['customer_id'] = customer.id
            return redirect('home')
        except Customer.DoesNotExist:
            messages.error(request, 'Invalid username or password')
    return render(request, 'market/customer_login.html')


def customer_logout(request):
    request.session.flush()
    return redirect('customer_login')


def staff_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        try:
            staff = Staff.objects.get(username=username, password=password)
            request.session['staff_id'] = staff.id
            return redirect('staff_dashboard')
        except Staff.DoesNotExist:
            messages.error(request, 'Invalid username or password')
    return render(request, 'market/staff_login.html')


def staff_logout(request):
    request.session.flush()
    return redirect('staff_login')


def home(request):
    if 'customer_id' not in request.session:
        return redirect('customer_login')
    return render(request, 'market/home.html')


def staff_dashboard(request):
    if 'staff_id' not in request.session:
        return redirect('staff_login')
    return render(request, 'market/staff_dashboard.html')