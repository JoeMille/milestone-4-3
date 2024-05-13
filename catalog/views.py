# Standard library imports
from django import forms
from django.conf import settings
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.mail import send_mail
from django.db.models import Prefetch
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.db import IntegrityError
from django.http import JsonResponse
from .forms import UserUpdateForm, UserProfileForm, AddToBasketForm, MessageForm
import stripe
import requests
from stripe.error import InvalidRequestError
from .forms import CustomUserCreationForm
from .models import Category, Product, Basket, BasketItem, ContactMessage, Sale, Order, OrderItem, UserProfile, Message
# Index page view


def index(request):

    basket = None
    if request.user.is_authenticated:
        basket, created = Basket.objects.get_or_create(user=request.user)

    featured_products = Product.objects.filter(featured=True)[:4]

    return render(request, 'catalog/index.html',
                  {'basket': basket, 'featured_products': featured_products})


def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            email = form.cleaned_data.get('email')
            house_number = form.cleaned_data.get('house_number')
            street_name = form.cleaned_data.get('street_name')
            town_city = form.cleaned_data.get('town_city')
            county = form.cleaned_data.get('county')
            eir_code = form.cleaned_data.get('eir_code')
            try:
                UserProfile.objects.create(
                    user=user,
                    house_number=house_number,
                    street_name=street_name,
                    town_city=town_city,
                    county=county,
                    eir_code=eir_code)
            except IntegrityError as e:
                print(e)
                return render(request,
                              'catalog/register.html',
                              {'form': form,
                               'error': 'Failed to create user profile.'})
            login(request, user)
            return redirect('index')
    else:
        form = CustomUserCreationForm()
    return render(request, 'catalog/register.html', {'form': form})

# Logout view


def logout(request):
    auth_logout(request)
    return redirect('index')

# About page view


def about(request):
    return render(request, 'catalog/about.html')

# Products page view


def products(request):
    categories = Category.objects.prefetch_related(
        Prefetch(
            'product_set',
            queryset=Product.objects.all().order_by('id'),
            to_attr='products'))
    return render(request, 'catalog/products.html', {'categories': categories})

# Product_detail view


def product_detail(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    return render(request, 'catalog/product_detail.html', {'product': product})

# Checkout page view


def checkout(request):
    if request.user.is_authenticated:
        basket, created = Basket.objects.get_or_create(user=request.user)
        for item in basket.basketitem_set.all():
            print(item.product.title)
        return render(request, 'catalog/checkout.html', {'basket': basket})
    else:
        return redirect('login')

# Add items to checkout basket
@login_required
def add_to_basket(request, product_id):
    if request.method == 'POST':
        product = get_object_or_404(Product, id=product_id)
        basket, created = Basket.objects.get_or_create(user=request.user)
        basket_item = BasketItem.objects.create(
            product=product,
            basket=basket,
            price=product.price,
            quantity=1,
        )
    return redirect('products')

# Remove items from checkout basket


def remove_from_basket(request, item_id):
    if request.method == 'POST':
        item = BasketItem.objects.get(id=item_id)
        item.delete()
    return redirect('checkout')

# Payment page view


def payment(request):
    return render(request, 'catalog/payment.html')

# Stripe payment view

def stripe_proxy(request):
    # Get the URL of the Stripe API endpoint from the client-side request
    url = request.GET.get('url')

    # Make a request to the Stripe API
    response = requests.get(url)

    # Return the response to the client-side code
    return JsonResponse(response.json())

@csrf_exempt
def charge(request):
    if request.method == 'POST':
        stripe.api_key = settings.STRIPE_SECRET_KEY
        token = request.POST['stripeToken']

        # Get the user's basket
        basket = Basket.objects.filter(user=request.user).first()
        if not basket:
            return HttpResponse('No items in basket', status=400)

        # Calculate the total cost of the items in the basket
        total_cost = 0
        for item in basket.basketitem_set.all():
            total_cost += item.product.price * item.quantity

        # Convert total_cost to pence (or the smallest currency unit)
        total_cost = int(total_cost * 100)

        # Create Stripe charge
        try:
            charge = stripe.Charge.create(
                amount=int(total_cost * 100),  # Convert total cost to cents
                currency='eur',  # Use euros
                description='Example charge',
                source=token,
            )
        except InvalidRequestError as e:
            return HttpResponse(f'Error: {str(e)}', status=400)

        # Create Order object
        try:
            order = Order.objects.create(
                user=request.user,
                total_cost=total_cost / 100,  # Add the total cost here
                # Add other necessary fields here
            )

            # Create OrderItem objects for each item in the basket
            for item in basket.basketitem_set.all():
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    quantity=item.quantity,
                    # Add other necessary fields here
                )

            # Clear the basket
            basket.basketitem_set.all().delete()

        except Exception as e:
            return HttpResponse(f'Error: {str(e)}', status=400)

        return redirect('charge')

    return render(request, 'catalog/charge.html')

# Created order item view


def create_order_item(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    order, created = Order.objects.get_or_create(
        user=request.user, status='pending', defaults={'total_cost': 0})
    order_item, created = OrderItem.objects.get_or_create(
        order=order, product=product, defaults={'quantity': 1})
    if not created:
        order_item.quantity += 1
        order_item.save()
    return redirect('charge')

# Dasboard view

@login_required
def dashboard(request):
    user = request.user
    profile = UserProfile.objects.filter(user=user).first()
    message_form = MessageForm()
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=profile)
        message_form = MessageForm(request.POST)
        if form.is_valid():
            form.save()
        if message_form.is_valid():
            Message.objects.create(user=request.user, text=message_form.cleaned_data['message'])
            return redirect('dashboard')
    else:
        form = UserProfileForm(instance=profile)
    return render(request, 'catalog/dashboard.html',
                  {'user': user, 'profile': profile, 'form': form, 'message_form': message_form})


@login_required
def profile(request):
    user = request.user
    profile = UserProfile.objects.get(user=user)
    return render(
        request, 'dashboard.html', {
            'user': user, 'profile': profile})
# login_view


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                auth_login(request, user)
                return redirect('index')
    else:
        form = AuthenticationForm()
    return render(request, 'catalog/login.html', {'form': form})
