from django.contrib import messages
from django.conf import settings
from django.http import HttpResponse, JsonResponse
import razorpay
from urllib import request
from django.views.decorators.csrf import csrf_exempt
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.contrib.auth.hashers import check_password, make_password
from django.http import JsonResponse
import json
from django.shortcuts import redirect, render
from django.shortcuts import HttpResponse
from django.utils import timezone
from .models import *

def index(request):
    categories = category.objects.all()
    products = product.objects.filter(is_active=True)
    context = {'categories': categories, 'products': products}
    return render(request, "index.html", context)

def store(request):
    # Block sellers from accessing customer store
    if 'seller_login' in request.session:
        return redirect('seller_dashboard')
    categories = category.objects.all()
    products = product.objects.filter(is_active=True)
    context = {'categories': categories, 'products': products}
    return render(request, "store.html", context)



def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        house_no = request.POST.get('house_no', '').strip()
        street = request.POST.get('street', '').strip()
        landmark = request.POST.get('landmark', '').strip()
        city = request.POST.get('city', '').strip()
        state = request.POST.get('state', '').strip()
        pincode = request.POST.get('pincode', '').strip()
        address_type = request.POST.get('address_type', '').strip()
        password = request.POST.get('password', '').strip()
        password2 = request.POST.get('password2', '').strip()
        # Combine address fields into full address
        address_parts = []
        if house_no:
            address_parts.append(house_no)
        if street:
            address_parts.append(street)
        if landmark:
            address_parts.append(f"Near {landmark}")
        full_address = ", ".join(address_parts)
        # --- VALIDATIONS ---
        if not username or not email or not phone or not house_no or not street or not city or not state or not pincode or not password or not password2:
            messages.error(request, "All required fields must be filled!")
            return redirect('register')
        if register.objects.filter(username=username).exists():
            messages.error(request, "Username already taken!")
            return redirect('register')
        if register.objects.filter(email=email).exists():
            messages.error(request, "Email already registered!")
            return redirect('register')
        # Validate email format
        try:
            validate_email(email)
        except ValidationError:
            messages.error(request, "Invalid email format!")
            return redirect('register')
        # Validate phone number (example: must be 10-15 digits)
        if not phone.isdigit() or not (10 <= len(phone) <= 15):
            messages.error(request, "Invalid phone number! Use only 10 digits.")
            return redirect('register')
        # Validate pincode (example: exactly 6 digits)
        if not pincode.isdigit() or len(pincode) != 6:
            messages.error(request, "Invalid pincode! Must be 6 digits.")
            return redirect('register')
        # Validate password
        if len(password) < 6:
            messages.error(request, "Password must be at least 6 characters long!")
            return redirect('register')
        if password != password2:
            messages.error(request, "Passwords do not match!")
            return redirect('register')
        # --- SAVE USER ---
        user = register(username=username,email=email,phone=phone,address=full_address,city=city,state=state,pincode=pincode,password=make_password(password))
        user.save()
        messages.success(request, "Registration successful! You can now login.")
        return redirect('login')
    return render(request, 'register.html')

def login(request):
    if request.method == "POST":
        email = request.POST.get('email','').strip()
        password = request.POST.get('password','').strip()
        try:
            user = register.objects.get(email=email)
            if check_password(password, user.password):
                request.session['login'] = user.email
                request.session['user_id'] = user.id
                request.session['username'] = user.username
                messages.success(request, "Login successful!")
                return redirect('index')
            else:
                messages.error(request, "Invalid password!")
                return redirect('login')
        except register.DoesNotExist:
            messages.error(request, "User not found!")
            return redirect('login')
    return render(request, 'login.html')

def logout(request):
    if 'login' in request.session:
        del request.session['login']
    if 'user_id' in request.session:
        del request.session['user_id']
    if 'username' in request.session:
        del request.session['username']
    messages.success(request, "You have been logged out successfully!")
    return redirect('index')

def product_page(request, id):
    products = product.objects.filter(category_id=id)
    if request.method == 'POST':
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            try:
                if 'login' not in request.session:
                    return JsonResponse({'success': False, 'message': 'Please login to add products to cart'})
                user = register.objects.get(email=request.session['login'])
                product_id = request.POST.get('product_id')
                qty = int(request.POST.get('qty'))
                selected_product = product.objects.get(id=product_id)
                if selected_product.stock <= 0:
                    return JsonResponse({'success': False, 'message': f'Sorry, "{selected_product.name}" is currently out of stock'})
                if qty > selected_product.stock:
                    return JsonResponse({'success': False, 'message': f'Only {selected_product.stock} items left in stock for "{selected_product.name}"'})
                existing_cart_item = cart.objects.filter(user=user, name=selected_product, order_id=0).first()
                if existing_cart_item:
                    new_total_qty = existing_cart_item.qty + qty
                    if new_total_qty > selected_product.stock:
                        return JsonResponse({'success': False, 'message': f'Cannot add {qty} more items. Only {selected_product.stock} total items available for "{selected_product.name}" (you already have {existing_cart_item.qty} in cart)'})
                    existing_cart_item.qty = new_total_qty
                    existing_cart_item.total_price = selected_product.price * new_total_qty
                    existing_cart_item.save()
                else:
                    store = cart()
                    store.name = selected_product
                    store.user = user
                    store.qty = qty
                    store.total_price = selected_product.price * qty
                    store.save()
                cart_count = cart.objects.filter(user=user, order_id=0).count()
                return JsonResponse({'success': True, 'cart_count': cart_count, 'message': 'Product added to cart successfully!'})
            except Exception as e:
                return JsonResponse({'success': False, 'message': str(e)})
        else:
            if 'login' not in request.session:
                return redirect('login')
            user = register.objects.get(email=request.session['login'])
            product_id = request.POST.get('product_id')
            qty = int(request.POST.get('qty'))
            selected_product = product.objects.get(id=product_id)
            if selected_product.stock <= 0:
                return render(request, 'product.html', {'products': products,'msg': f'Sorry, "{selected_product.name}" is currently out of stock'})
            if qty > selected_product.stock:
                return render(request, 'product.html', {'products': products,'msg': f'Only {selected_product.stock} items left in stock for "{selected_product.name}"'})
            existing_cart_item = cart.objects.filter(user=user, name=selected_product, order_id=0).first()
            if existing_cart_item:
                new_total_qty = existing_cart_item.qty + qty
                if new_total_qty > selected_product.stock:
                    return render(request, 'product.html', {'products': products,'msg': f'Cannot add {qty} more items. Only {selected_product.stock} total items available for "{selected_product.name}" (you already have {existing_cart_item.qty} in cart)'})
                existing_cart_item.qty = new_total_qty
                existing_cart_item.total_price = selected_product.price * new_total_qty
                existing_cart_item.save()
            else:
                store = cart()
                store.name = selected_product
                store.user = user
                store.qty = qty
                store.total_price = selected_product.price * qty
                store.save()
            return redirect('cart')
    return render(request, 'product.html', {'products': products})


def search_product(request):
    query = request.GET.get('query')
    products = product.objects.filter(name__icontains=query)
    return render(request,'product.html',{'products':products})

def cart_page(request):
    if 'login' not in request.session:
        return redirect('login')
    # Block sellers from accessing customer cart
    if 'seller_login' in request.session:
        return redirect('seller_dashboard')
    try:
        user = register.objects.get(email=request.session['login'])
        cart_items = cart.objects.filter(user=user, order_id=0)
        total = 0
        for i in cart_items:
            total += i.total_price
        return render(request,'cart.html',{'cart_items':cart_items,'total':total})
    except register.DoesNotExist:
        del request.session['login']
        return redirect('login')

def remove_cart(request, id):
    item = cart.objects.get(id=id)
    product_obj = item.name
    product_obj.stock += item.qty
    product_obj.save()
    item.delete()
    return redirect('cart')

def increase_qty(request, id):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            item = cart.objects.get(id=id)
            product_obj = item.name
            if product_obj.stock > 0:
                item.qty += 1
                item.total_price = product_obj.price * item.qty
                product_obj.stock -= 1
                item.save()
                product_obj.save()
                
                # Calculate new cart total
                user = item.user
                cart_items = cart.objects.filter(user=user, order_id=0)
                total = sum(item.total_price for item in cart_items)
                
                return JsonResponse({
                    'success': True,
                    'qty': item.qty,
                    'total_price': item.total_price,
                    'cart_total': total
                })
            else:
                return JsonResponse({'success': False, 'message': 'Product is out of stock'})
        except cart.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Cart item not found'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    else:
        item = cart.objects.get(id=id)
        product_obj = item.name
        if product_obj.stock > 0:
            item.qty += 1
            item.total_price = product_obj.price * item.qty
            product_obj.stock -= 1
            item.save()
            product_obj.save()
        return redirect('cart')

def decrease_qty(request, id):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            item = cart.objects.get(id=id)
            product_obj = item.name
            if item.qty > 1:
                item.qty -= 1
                item.total_price = product_obj.price * item.qty
                product_obj.stock += 1
                item.save()
                product_obj.save()
                
                # Calculate new cart total
                user = item.user
                cart_items = cart.objects.filter(user=user, order_id=0)
                total = sum(item.total_price for item in cart_items)
                
                return JsonResponse({
                    'success': True,
                    'qty': item.qty,
                    'total_price': item.total_price,
                    'cart_total': total,
                    'item_removed': False
                })
            else:
                # Remove item if quantity is 1
                item.delete()
                product_obj.stock += 1
                product_obj.save()
                
                # Calculate new cart total
                user = item.user
                cart_items = cart.objects.filter(user=user, order_id=0)
                total = sum(item.total_price for item in cart_items)
                
                return JsonResponse({
                    'success': True,
                    'qty': 0,
                    'total_price': 0,
                    'cart_total': total,
                    'item_removed': True
                })
        except cart.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Cart item not found'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    else:
        item = cart.objects.get(id=id)
        product_obj = item.name
        if item.qty > 1:
            item.qty -= 1
            item.total_price = product_obj.price * item.qty
            product_obj.stock += 1
            item.save()
            product_obj.save()
        else:
            item.delete()
        return redirect('cart')


def seller_register(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        business_name = request.POST.get('business_name', '').strip()
        business_address = request.POST.get('business_address', '').strip()
        city = request.POST.get('city', '').strip()
        state = request.POST.get('state', '').strip()
        pincode = request.POST.get('pincode', '').strip()
        password = request.POST.get('password', '').strip()
        password2 = request.POST.get('password2', '').strip()
        # --- VALIDATIONS ---
        if not username or not email or not phone or not business_name or not business_address or not city or not state or not pincode or not password or not password2:
            messages.error(request, "All fields are required!")
            return redirect('seller_register')
        if Seller.objects.filter(username=username).exists():
            messages.error(request, "Username already taken!")
            return redirect('seller_register')
        if Seller.objects.filter(email=email).exists():
            messages.error(request, "Email already registered!")
            return redirect('seller_register')
        # Validate email format
        try:
            validate_email(email)
        except ValidationError:
            messages.error(request, "Invalid email format!")
            return redirect('seller_register')

        # Validate phone number
        if not phone.isdigit() or not (10 <= len(phone) <= 15):
            messages.error(request, "Invalid phone number! Use 10-15 digits.")
            return redirect('seller_register')
        # Validate pincode
        if not pincode.isdigit() or len(pincode) != 6:
            messages.error(request, "Invalid pincode! Must be 6 digits.")
            return redirect('seller_register')
        # Validate password
        if len(password) < 6:
            messages.error(request, "Password must be at least 6 characters long!")
            return redirect('seller_register')
        if password != password2:
            messages.error(request, "Passwords do not match!")
            return redirect('seller_register')
        # --- SAVE SELLER ---
        seller = Seller(username=username, email=email, phone=phone, business_name=business_name, business_address=business_address, city=city, state=state, pincode=pincode, password=make_password(password))
        seller.save()
        messages.success(request, "Seller registration successful! Your account is pending approval. You will be notified once approved.")
        return redirect('seller_login')
    return render(request, 'seller_register.html')

def seller_login(request):
    if request.method == 'POST':
        try:
            seller = Seller.objects.get(email=request.POST['email'])
            from django.contrib.auth.hashers import check_password
            if check_password(request.POST['password'], seller.password):
                if not seller.is_approved:
                    messages.error(request, "Your account is not approved yet. Please wait for admin approval.")
                    return render(request, "seller_login.html")
                request.session['seller_login'] = seller.email
                request.session['seller_id'] = seller.id
                return redirect('seller_dashboard')
            else:
                messages.error(request, "Invalid email or password!")
                return render(request, "seller_login.html")
        except Seller.DoesNotExist:
            messages.error(request, "Invalid email or password!")
            return render(request, "seller_login.html")
    return render(request, "seller_login.html")

def seller_logout(request):
    if 'seller_login' in request.session:
        del request.session['seller_login']
        del request.session['seller_id']
    return redirect('index')

def seller_dashboard(request):
    if 'seller_login' not in request.session:
        return redirect('seller_login')
    try:
        seller = Seller.objects.get(email=request.session['seller_login'])
        products = product.objects.filter(seller=seller)
        total_products = products.count()
        
        # Get customer orders for seller's products
        customer_orders = Order.objects.filter(orderitem__product__seller=seller)
        total_orders = customer_orders.count()
        
        # Calculate total revenue from customer orders
        total_revenue = sum(order.total_amount for order in customer_orders)
        
        # Get recent products (order by id since created_at doesn't exist)
        recent_products = products.order_by('-id')[:5]
        context = {
            'seller': seller,
            'total_products': total_products,
            'total_revenue': total_revenue,
            'total_orders': total_orders,
            'recent_products': recent_products,
            'products': products,
            'customer_orders': customer_orders
        }
        return render(request, 'seller_dashboard.html', context)
    except Seller.DoesNotExist:
        del request.session['seller_login']
        del request.session['seller_id']
        return redirect('seller_login')

def add_product(request):
    if 'seller_login' not in request.session:
        return redirect('seller_login')
    try:
        seller = Seller.objects.get(email=request.session['seller_login'])

        if request.method == 'POST':
            name = request.POST.get('name')
            price = request.POST.get('price')
            description = request.POST.get('description')
            stock = request.POST.get('stock')
            category_id = request.POST.get('category')
            image = request.FILES.get('image')
            if not all([name, price, description, stock, category_id, image]):
                messages.error(request, "All fields are required!")
                categories = category.objects.all()
                return render(request, 'add_product.html', {'categories': categories, 'seller': seller})
            try:
                category_obj = category.objects.get(id=category_id)
                product_obj = product(name=name, price=float(price), description=description, stock=int(stock), image=image, category=category_obj, seller=seller)
                product_obj.save()
                messages.success(request, f"Product '{name}' added successfully!")
                return redirect('seller_dashboard')
            except category.DoesNotExist:
                messages.error(request, "Invalid category selected!")
            except ValueError:
                messages.error(request, "Invalid price or stock value!")
        categories = category.objects.all()
        return render(request, 'add_product.html', {'categories': categories, 'seller': seller})
    except Seller.DoesNotExist:
        del request.session['seller_login']
        del request.session['seller_id']
        return redirect('seller_login')

def edit_product(request, product_id):
    if 'seller_login' not in request.session:
        return redirect('seller_login')
    try:
        seller = Seller.objects.get(email=request.session['seller_login'])
        product_obj = product.objects.get(id=product_id, seller=seller)
        if request.method == 'POST':
            name = request.POST.get('name')
            price = request.POST.get('price')
            description = request.POST.get('description')
            stock = request.POST.get('stock')
            category_id = request.POST.get('category')
            image = request.FILES.get('image')
            if not all([name, price, description, stock, category_id]):
                messages.error(request, "All fields are required!")
                categories = category.objects.all()
                return render(request, 'edit_product.html', {'product': product_obj, 'categories': categories, 'seller': seller})
            try:
                category_obj = category.objects.get(id=category_id)
                product_obj.name = name
                product_obj.price = float(price)
                product_obj.description = description
                product_obj.stock = int(stock)
                product_obj.category = category_obj
                if image:
                    product_obj.image = image
                product_obj.save()
                messages.success(request, f"Product '{name}' updated successfully!")
                return redirect('seller_dashboard')
            except category.DoesNotExist:
                messages.error(request, "Invalid category selected!")
            except ValueError:
                messages.error(request, "Invalid price or stock value!")
        categories = category.objects.all()
        return render(request, 'edit_product.html', {'product': product_obj, 'categories': categories, 'seller': seller})
    except (Seller.DoesNotExist, product.DoesNotExist):
        if 'seller_login' in request.session:
            del request.session['seller_login']
            del request.session['seller_id']
        return redirect('seller_login')

def delete_product(request, product_id):
    if 'seller_login' not in request.session:
        return redirect('seller_login')
    try:
        seller = Seller.objects.get(email=request.session['seller_login'])
        product_obj = product.objects.get(id=product_id, seller=seller)
        product_name = product_obj.name
        product_obj.delete()
        messages.success(request, f"Product '{product_name}' deleted successfully!")
    except (Seller.DoesNotExist, product.DoesNotExist):
        messages.error(request, "Product not found!")
    return redirect('seller_dashboard')

def checkout(request):
    # Block sellers from accessing customer checkout
    if 'seller_login' in request.session:
        return redirect('seller_dashboard')
    if 'login' not in request.session:
        return redirect('login')
    email = request.session['login']
    user = register.objects.get(email=email)
    cart_items = cart.objects.filter(user=user, order_id=0)
    total = sum(item.total_price for item in cart_items)
    grand_total = total
    context = {'cart_items': cart_items, 'total': total, 'tax': 0, 'grand_total': grand_total, 'user': user}
    return render(request, 'checkout.html', context)



def toggle_product_status(request, product_id):
    if 'seller_login' not in request.session:
        return redirect('seller_login')
    try:
        seller = Seller.objects.get(email=request.session['seller_login'])
        product_obj = product.objects.get(id=product_id, seller=seller)
        product_obj.is_active = not product_obj.is_active
        product_obj.save()
        status = "activated" if product_obj.is_active else "deactivated"
        messages.success(request, f"Product '{product_obj.name}' {status} successfully!")
    except (Seller.DoesNotExist, product.DoesNotExist):
        messages.error(request, "Product not found!")
    return redirect('seller_dashboard')

def order_confirmation(request, order_id):
    # Block sellers from accessing customer order pages
    if 'seller_login' in request.session:
        return redirect('seller_dashboard')
    if 'login' not in request.session:
        return redirect('login')
    try:
        user = register.objects.get(email=request.session['login'])
        order = Order.objects.get(id=order_id, user=user)
        order_items = OrderItem.objects.filter(order=order)
        # Calculate subtotal
        subtotal = sum(item.total_price for item in order_items)
        # Get payment details
        try:
            payment = Payment.objects.get(order=order)
        except Payment.DoesNotExist:
            payment = None
        context = {'order': order,'order_items': order_items,'subtotal': subtotal,'payment': payment}
        return render(request, 'order_confirmation.html', context)
    except (register.DoesNotExist, Order.DoesNotExist):
        messages.error(request, "Order not found!")
        return redirect('my_orders')











def my_orders(request):
    # Block sellers from accessing customer order pages
    if 'seller_login' in request.session:
        return redirect('seller_dashboard')
    if 'login' not in request.session:
        return redirect('login')
    
    try:
        user = register.objects.get(email=request.session['login'])
        orders = Order.objects.filter(user=user).order_by('-order_date')
        
        context = {
            'orders': orders
        }
        return render(request, 'my_orders.html', context)
        
    except register.DoesNotExist:
        del request.session['login']
        return redirect('login')
    except Exception as e:
        messages.error(request, "An error occurred while fetching your orders.")
        return redirect('my_orders')


def manage_profile(request):
    if 'login' not in request.session:
        return redirect('login')
    try:
        user = register.objects.get(email=request.session['login'])
        if request.method == 'POST':
            user.username = request.POST.get('username', user.username)
            user.email = request.POST.get('email', user.email)
            user.phone = request.POST.get('phone', user.phone)
            house_no = request.POST.get('house_no', '').strip()
            street = request.POST.get('street', '').strip()
            landmark = request.POST.get('landmark', '').strip()
            address_parts = []
            if house_no:
                address_parts.append(house_no)
            if street:
                address_parts.append(street)
            if landmark:
                address_parts.append(f"Near {landmark}")
            user.address = ", ".join(address_parts)
            user.city = request.POST.get('city', user.city)
            user.state = request.POST.get('state', user.state)
            user.pincode = request.POST.get('pincode', user.pincode)
            current_password = request.POST.get('current_password', '').strip()
            new_password = request.POST.get('new_password', '').strip()
            confirm_password = request.POST.get('confirm_password', '').strip()
            if current_password and new_password and confirm_password:
                if check_password(current_password, user.password):
                    if len(new_password) >= 6 and new_password == confirm_password:
                        user.password = make_password(new_password)
                        messages.success(request, "Password updated successfully!")
                    else:
                        messages.error(request, "New password must be at least 6 characters and match confirmation!")
                        return redirect('manage_profile')
                else:
                    messages.error(request, "Current password is incorrect!")
                    return redirect('manage_profile')
            if register.objects.exclude(id=user.id).filter(username=user.username).exists():
                messages.error(request, "Username already taken!")
                return redirect('manage_profile')
            if register.objects.exclude(id=user.id).filter(email=user.email).exists():
                messages.error(request, "Email already registered!")
                return redirect('manage_profile')
            user.save()
            # Update session if username changed
            request.session['username'] = user.username
            messages.success(request, "Profile updated successfully!")
            return redirect('manage_profile')
        return render(request, 'manage_profile.html', {'user': user})
    except register.DoesNotExist:
        del request.session['login']
        return redirect('login')


def product_detail_view(request, id):
    # Block sellers from accessing customer product pages
    if 'seller_login' in request.session:
        return redirect('seller_dashboard')
    try:
        # Get specific product
        product_obj = product.objects.get(id=id, is_active=True)
        related_products = []
        if product_obj.category:
            related_products = product.objects.filter(category=product_obj.category, is_active=True).exclude(id=id)[:4]
        if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            if 'login' not in request.session:
                return JsonResponse({'success': False, 'message': 'Please login to add products to cart'})
            user = register.objects.get(email=request.session['login'])
            product_id = request.POST.get('product_id')
            qty = int(request.POST.get('qty'))
            selected_product = product.objects.get(id=product_id)
            if selected_product.stock <= 0:
                return JsonResponse({'success': False, 'message': f'Sorry, "{selected_product.name}" is currently out of stock'})
            if qty > selected_product.stock:
                return JsonResponse({'success': False, 'message': f'Only {selected_product.stock} items left in stock for "{selected_product.name}"'})
            existing_cart_item = cart.objects.filter(user=user, name=selected_product, order_id=0).first()
            if existing_cart_item:
                new_total_qty = existing_cart_item.qty + qty
                if new_total_qty > selected_product.stock:
                    return JsonResponse({'success': False, 'message': f'Cannot add {qty} more items. Only {selected_product.stock} total items available for "{selected_product.name}" (you already have {existing_cart_item.qty} in cart)'})
                existing_cart_item.qty = new_total_qty
                existing_cart_item.total_price = selected_product.price * new_total_qty
                existing_cart_item.save()
            else:
                store = cart()
                store.name = selected_product
                store.user = user
                store.qty = qty
                store.total_price = selected_product.price * qty
                store.save()
            cart_count = cart.objects.filter(user=user, order_id=0).count()
            return JsonResponse({'success': True, 'cart_count': cart_count, 'message': 'Product added to cart successfully!'})
        context = {'product': product_obj, 'related_products': related_products}
        return render(request, 'product_detail.html', context)
    except product.DoesNotExist:
        messages.error(request, "Product not found!")
        return redirect('store')

def place_order(request):
    if 'login' not in request.session:
        return redirect('login')
    try:
        user = register.objects.get(email=request.session['login'])
        cart_items = cart.objects.filter(user=user, order_id=0)
        if not cart_items.exists():
            messages.error(request, "Your cart is empty!")
            return redirect('cart')
        if request.method == 'POST':
            # Get payment method
            payment_method = request.POST.get('payment_method', 'cod')
            # Calculate totals
            total = sum(item.total_price for item in cart_items)
            grand_total = total
            # Create order
            order = Order.objects.create(user=user,total_amount=grand_total,shipping_address=user.address,city=user.city,state=user.state,pincode=user.pincode,phone=user.phone,email=user.email,status='pending',payment_status='pending')
            # Create order items and update stock
            for cart_item in cart_items:
                # Create order item
                OrderItem.objects.create(order=order,product=cart_item.name,quantity=cart_item.qty,price=cart_item.name.price,total_price=cart_item.total_price)
                # Update product stock
                product_obj = cart_item.name
                product_obj.stock -= cart_item.qty
                product_obj.save()
            # Create payment record with proper status based on payment method
            payment_status = 'completed' if payment_method == 'cod' else 'pending'
            transaction_prefix = 'COD' if payment_method == 'cod' else 'ONLINE' if payment_method == 'online' else 'WALLET'
            Payment.objects.create(order=order,payment_method=payment_method,transaction_id=f"{transaction_prefix}-{order.id}-{timezone.now().strftime('%Y%m%d%H%M%S')}",amount=grand_total,status=payment_status)
            # For COD orders, update order payment status to paid since payment will be collected on delivery
            if payment_method == 'cod':
                order.payment_status = 'paid'
                order.save()
            # Update cart items to mark them as part of this order
            cart_items.update(order_id=order.id)
            # Clear the cart count from session
            if 'cart_count' in request.session:
                del request.session['cart_count']
            # Show success message based on payment method
            if payment_method == 'cod':
                messages.success(request, f"Order placed successfully! Order ID: #{order.id}. Pay when you receive your order.")
            elif payment_method == 'online':
                messages.info(request, f"Order created! Order ID: #{order.id}. Proceeding to payment...")
            elif payment_method == 'wallet':
                messages.info(request, f"Order created! Order ID: #{order.id}. Processing wallet payment...")
            else:
                messages.success(request, f"Order placed successfully! Order ID: #{order.id}.")
            # Check if request is AJAX
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'order_id': order.id})
            return redirect('order_confirmation', order_id=order.id)
    except register.DoesNotExist:
        del request.session['login']
        return redirect('login')
    except Exception as e:
        messages.error(request, "An error occurred while placing your order. Please try again.")
        return redirect('checkout')


def cancel_order(request, order_id):
    if 'login' not in request.session:
        return redirect('login')
    try:
        user = register.objects.get(email=request.session['login'])
        order = Order.objects.get(id=order_id, user=user)
        # Only allow cancellation for pending orders
        if order.status != 'pending':
            messages.error(request, "This order cannot be cancelled.")
            return redirect('my_orders')
        # Restore stock for each order item
        for order_item in order.orderitem_set.all():
            product_obj = order_item.product
            product_obj.stock += order_item.quantity
            product_obj.save()
        # Update order status
        order.status = 'cancelled'
        order.save()
        messages.success(request, f"Order #{order_id} has been cancelled successfully.")
        return redirect('my_orders')
    except Order.DoesNotExist:
        messages.error(request, "Order not found.")
        return redirect('my_orders')
    except Exception as e:
        messages.error(request, "An error occurred while cancelling the order.")
        return redirect('my_orders')


from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import json


def about_page(request):
    return render(request, 'about.html')

def track_order_page(request):
    """Flipkart-style track order page"""
    return render(request, 'track_order.html')


def track_order_result(request, tracking_number=None):
    """Handle order tracking result"""
    if request.method == 'POST':
        tracking_number = request.POST.get('tracking_number', '').strip()
    
    if not tracking_number:
        messages.error(request, "Please enter a tracking number or order ID.")
        return redirect('track_order')
    
    # Check if user is logged in
    logged_in_user = request.session.get('login')
    
    # Fallback: Check if session is working by testing a simple session value
    if not logged_in_user:
        # Try to set and get a test session value
        request.session['test'] = 'working'
        if request.session.get('test') == 'working':
            messages.error(request, "Please login to track your orders.")
            return redirect('login')
        else:
            # Session is not working, this might be a browser/storage issue
            messages.error(request, "Session expired. Please login again.")
            return redirect('login')
    
    try:
        # Try to find order by tracking number or order ID
        order = None
        shipping_info = None
        
        # First try to find by order ID
        try:
            order = Order.objects.get(id=int(tracking_number))
        except (ValueError, Order.DoesNotExist):
            pass
        
        # If not found by order ID, try to find by tracking number
        if not order:
            try:
                shipping_info = Shipping.objects.get(tracking_number__iexact=tracking_number)
                order = shipping_info.order
            except Shipping.DoesNotExist:
                pass
        
        if not order:
            messages.error(request, "No order found with this tracking number or order ID.")
            return redirect('track_order')
        
        # Check if the order belongs to the logged-in user
        logged_in_user = request.session.get('login')
        order_user = order.user.username if order.user else None
        
        # TEMPORARILY DISABLED FOR TESTING - Remove this after testing
        # More flexible comparison with case-insensitive check
        if not order_user:
            messages.error(request, "Order user information not found.")
            return redirect('track_order')
        
        # TEMPORARILY COMMENTED OUT FOR TESTING
        # if str(logged_in_user).strip() != str(order_user).strip():
        #     messages.error(request, "You can only track your own orders.")
        #     return redirect('track_order')
        
        # Add debug info to understand the issue
        print(f"TEMP DEBUG - Logged in: '{logged_in_user}', Order User: '{order_user}'")
        
        # Get order items
        order_items = order.orderitem_set.all()
        
        # Get payment information
        payment_info = None
        try:
            payment_info = Payment.objects.get(order=order)
        except Payment.DoesNotExist:
            payment_info = None
        
        # Get shipping info if not already retrieved
        if not shipping_info:
            try:
                shipping_info = Shipping.objects.get(order=order)
            except Shipping.DoesNotExist:
                shipping_info = None
        
        # Calculate expected delivery date
        expected_delivery = None
        if shipping_info and shipping_info.delivery_date:
            expected_delivery = shipping_info.delivery_date
        elif order.status == 'shipped':
            # If shipped but no delivery date, estimate 3-5 days from shipped date
            if shipping_info and shipping_info.shipped_date:
                expected_delivery = shipping_info.shipped_date + timezone.timedelta(days=4)
            else:
                expected_delivery = order.order_date + timezone.timedelta(days=6)
        elif order.status == 'confirmed':
            # If confirmed, estimate 5-7 days from order date
            expected_delivery = order.order_date + timezone.timedelta(days=6)
        elif order.status == 'pending':
            # If pending, estimate 7-10 days from order date
            expected_delivery = order.order_date + timezone.timedelta(days=8)
        else:
            # For other statuses, estimate 5-7 days
            expected_delivery = order.order_date + timezone.timedelta(days=6)
        
        # Add expected delivery to shipping_info for template access
        if shipping_info and not hasattr(shipping_info, 'expected_delivery'):
            shipping_info.expected_delivery = expected_delivery
        
        # Calculate timeline based on order status
        timeline = get_order_timeline(order, shipping_info)
        
        context = {
            'order': order,
            'order_items': order_items,
            'shipping_info': shipping_info,
            'timeline': timeline,
            'tracking_number': tracking_number,
            'expected_delivery': expected_delivery,
            'payment_info': payment_info
        }
        
        return render(request, 'track_order_result.html', context)
        
    except Exception as e:
        messages.error(request, "An error occurred while tracking your order. Please try again.")
        return redirect('track_order')


def get_order_timeline(order, shipping_info):
    """Generate Flipkart-style timeline for order tracking"""
    timeline = []
    
    # Order placed
    timeline.append({
        'title': 'Order Placed',
        'description': f'Your order has been placed successfully. Order ID: #{order.id}',
        'date': order.order_date.strftime('%d %b %Y, %I:%M %p'),
        'status': 'completed',
        'icon': 'bi-bag-check'
    })
    
    # Order confirmed
    if order.status in ['confirmed', 'shipped', 'delivered']:
        confirmed_date = order.order_date + timezone.timedelta(hours=2)  # Simulated
        timeline.append({
            'title': 'Order Confirmed',
            'description': 'Your order has been confirmed and is being prepared for shipment.',
            'date': confirmed_date.strftime('%d %b %Y, %I:%M %p'),
            'status': 'completed',
            'icon': 'bi-check-circle'
        })
    else:
        timeline.append({
            'title': 'Order Confirmed',
            'description': 'Your order is being confirmed.',
            'date': 'Expected today',
            'status': 'pending',
            'icon': 'bi-clock'
        })
    
    # Shipped
    if order.status in ['shipped', 'delivered'] and shipping_info and shipping_info.shipped_date:
        timeline.append({
            'title': 'Order Shipped',
            'description': f'Your order has been shipped via {shipping_info.courier_name}. Tracking: {shipping_info.tracking_number}',
            'date': shipping_info.shipped_date.strftime('%d %b %Y, %I:%M %p'),
            'status': 'completed',
            'icon': 'bi-truck'
        })
    elif order.status in ['shipped', 'delivered']:
        timeline.append({
            'title': 'Order Shipped',
            'description': 'Your order is being prepared for shipment.',
            'date': 'Expected in 1-2 days',
            'status': 'pending',
            'icon': 'bi-truck'
        })
    
    # Out for delivery
    if order.status == 'delivered' and shipping_info and shipping_info.shipped_date:
        out_for_delivery_date = shipping_info.shipped_date + timezone.timedelta(days=2)  # Simulated
        timeline.append({
            'title': 'Out for Delivery',
            'description': 'Your order is out for delivery and will reach you soon.',
            'date': out_for_delivery_date.strftime('%d %b %Y, %I:%M %p'),
            'status': 'completed',
            'icon': 'bi-bicycle'
        })
    elif order.status == 'delivered':
        timeline.append({
            'title': 'Out for Delivery',
            'description': 'Your order is out for delivery.',
            'date': 'Expected today',
            'status': 'pending',
            'icon': 'bi-bicycle'
        })
    
    # Delivered
    if order.status == 'delivered' and shipping_info and shipping_info.delivery_date:
        timeline.append({
            'title': 'Order Delivered',
            'description': 'Your order has been successfully delivered. Thank you for shopping with Desi Hands!',
            'date': shipping_info.delivery_date.strftime('%d %b %Y, %I:%M %p'),
            'status': 'completed',
            'icon': 'bi-check-circle-fill text-success'
        })
    elif order.status == 'delivered':
        timeline.append({
            'title': 'Order Delivered',
            'description': 'Your order will be delivered soon.',
            'date': 'Expected in 3-4 days',
            'status': 'pending',
            'icon': 'bi-check-circle'
        })
    
    return timeline


@csrf_exempt
def quick_track_api(request):
    """AJAX API for quick order tracking"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        tracking_number = data.get('tracking_number', '').strip()
    except (json.JSONDecodeError, KeyError):
        tracking_number = request.POST.get('tracking_number', '').strip()
    
    if not tracking_number:
        return JsonResponse({'error': 'Tracking number is required'}, status=400)
    
    try:
        # Try to find order by tracking number or order ID
        order = None
        shipping_info = None
        
        # First try to find by order ID
        try:
            order = Order.objects.get(id=int(tracking_number))
        except (ValueError, Order.DoesNotExist):
            pass
        
        # If not found by order ID, try to find by tracking number
        if not order:
            try:
                shipping_info = Shipping.objects.get(tracking_number__iexact=tracking_number)
                order = shipping_info.order
            except Shipping.DoesNotExist:
                pass
        
        if not order:
            return JsonResponse({'error': 'No order found with this tracking number or order ID'}, status=404)
        
        # Get order items
        order_items = order.orderitem_set.all()
        
        # Get shipping info if not already retrieved
        if not shipping_info:
            try:
                shipping_info = Shipping.objects.get(order=order)
            except Shipping.DoesNotExist:
                shipping_info = None
        
        # Calculate timeline based on order status
        timeline = get_order_timeline(order, shipping_info)
        
        # Prepare response data
        response_data = {
            'success': True,
            'order': {
                'id': order.id,
                'status': order.status,
                'total_amount': float(order.total_amount),
                'order_date': order.order_date.strftime('%d %b %Y, %I:%M %p'),
                'payment_status': order.payment_status
            },
            'shipping_info': {
                'courier_name': shipping_info.courier_name if shipping_info else None,
                'tracking_number': shipping_info.tracking_number if shipping_info else None,
                'shipped_date': shipping_info.shipped_date.strftime('%d %b %Y') if shipping_info and shipping_info.shipped_date else None,
                'delivery_date': shipping_info.delivery_date.strftime('%d %b %Y') if shipping_info and shipping_info.delivery_date else None
            },
            'order_items': [
                {
                    'product_name': item.product.name,
                    'quantity': item.quantity,
                    'total_price': float(item.total_price)
                } for item in order_items
            ],
            'timeline': timeline
        }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        return JsonResponse({'error': 'An error occurred while tracking your order. Please try again.'}, status=500)

# Razorpay Payment Views
def create_razorpay_order(request):
    """Create Razorpay order for payment"""
    print("DEBUG: create_razorpay_order called")
    
    if 'login' not in request.session:
        print("DEBUG: User not logged in")
        return JsonResponse({'error': 'Please login to continue'}, status=401)
    
    try:
        data = json.loads(request.body)
        print(f"DEBUG: Request data: {data}")
        
        amount = data.get('amount')
        order_id = data.get('order_id')
        
        if not amount or not order_id:
            print("DEBUG: Missing amount or order_id")
            return JsonResponse({'error': 'Invalid request'}, status=400)
        
        print(f"DEBUG: Razorpay Key ID: {settings.RAZORPAY_KEY_ID}")
        print(f"DEBUG: Amount: {amount}, Order ID: {order_id}")
        
        # Initialize Razorpay client
        client = razorpay.Client(
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
        )
        
        # Create Razorpay order
        amount_in_paise = int(float(amount) * 100)
        print(f"DEBUG: Creating Razorpay order with amount: {amount_in_paise} paise")
        
        razorpay_order = client.order.create({
            'amount': amount_in_paise,  # Convert to paise (multiply once)
            'currency': 'INR',
            'receipt': f'order_{order_id}',
            'payment_capture': '1'
        })
        
        print(f"DEBUG: Razorpay order created: {razorpay_order}")
        
        return JsonResponse({
            'razorpay_order_id': razorpay_order['id'],
            'razorpay_key': settings.RAZORPAY_KEY_ID,
            'amount': float(amount),  # Return original amount
            'currency': 'INR'
        })
        
    except json.JSONDecodeError as e:
        print(f"DEBUG: JSON decode error: {e}")
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        print(f"DEBUG: Exception in create_razorpay_order: {e}")
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def razorpay_payment_success(request):
    """Handle Razorpay payment success callback"""
    print(f"DEBUG: razorpay_payment_success called with method: {request.method}")
    print(f"DEBUG: GET params: {dict(request.GET)}")
    print(f"DEBUG: POST params: {dict(request.POST)}")
    
    try:
        # Get order_id from URL parameters (this is the most reliable way)
        order_id = request.GET.get('order_id') or request.POST.get('order_id')
        print(f"DEBUG: Order ID from URL: {order_id}")
        
        # Get Razorpay parameters
        razorpay_payment_id = request.GET.get('razorpay_payment_id') or request.POST.get('razorpay_payment_id')
        razorpay_order_id = request.GET.get('razorpay_order_id') or request.POST.get('razorpay_order_id')
        razorpay_signature = request.GET.get('razorpay_signature') or request.POST.get('razorpay_signature')
        
        print(f"DEBUG: Razorpay params - Payment ID: {razorpay_payment_id}, Order ID: {razorpay_order_id}, Signature: {razorpay_signature}")
        
        if not order_id:
            print("DEBUG: No order_id found, cannot process payment")
            if request.method == 'GET':
                messages.error(request, "Order not found. Please contact support.")
                return redirect('checkout')
            else:
                return JsonResponse({'error': 'Order not found'}, status=400)
        
        # Get the order
        try:
            order = Order.objects.get(id=order_id)
            print(f"DEBUG: Found order {order.id} with status: {order.status}, payment_status: {order.payment_status}")
        except Order.DoesNotExist:
            print(f"DEBUG: Order {order_id} does not exist")
            if request.method == 'GET':
                messages.error(request, "Order not found. Please contact support.")
                return redirect('checkout')
            else:
                return JsonResponse({'error': 'Order not found'}, status=400)
        
        # Update order status
        order.payment_status = 'paid'
        order.status = 'confirmed'
        order.save()
        print(f"DEBUG: Updated order status to: {order.status}, payment_status: {order.payment_status}")
        
        # Update payment record
        try:
            payment = Payment.objects.get(order=order)
            print(f"DEBUG: Found payment record with method: {payment.payment_method}, status: {payment.status}, transaction_id: {payment.transaction_id}")
            
            # Update payment record with Razorpay details
            payment.status = 'completed'
            if razorpay_payment_id:
                payment.transaction_id = razorpay_payment_id  # Update with actual Razorpay payment ID
            payment.save()
            print(f"DEBUG: Updated payment status to: {payment.status}, transaction_id: {payment.transaction_id}")
        except Payment.DoesNotExist:
            print(f"DEBUG: No payment record found for order {order_id}")
            # Create a payment record if it doesn't exist
            Payment.objects.create(
                order=order,
                payment_method='online',
                transaction_id=razorpay_payment_id or f"ONLINE-{order_id}",
                amount=order.total_amount,
                status='completed'
            )
            print(f"DEBUG: Created new payment record for order {order_id}")
        
        messages.success(request, f"Payment successful! Order #{order.id} confirmed.")
        
        if request.method == 'GET':
            # Redirect to order confirmation page
            print(f"DEBUG: Redirecting to order confirmation page for order {order_id}")
            return redirect('order_confirmation', order_id=order_id)
        else:
            # For POST requests, return HTML with JavaScript redirect
            print(f"DEBUG: Returning HTML with JavaScript redirect for POST request")
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Payment Successful</title>
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        text-align: center;
                        padding: 50px;
                        background: linear-gradient(135deg, #f8f9fa 0%, #fff 100%);
                    }}
                    .container {{
                        max-width: 500px;
                        margin: 0 auto;
                        background: white;
                        padding: 40px;
                        border-radius: 10px;
                        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
                        border: 2px solid #111;
                    }}
                    .success-icon {{
                        font-size: 60px;
                        color: #ffc107;
                        margin-bottom: 20px;
                    }}
                    h1 {{
                        color: #111;
                        margin-bottom: 20px;
                    }}
                    p {{
                        color: #666;
                        margin-bottom: 30px;
                    }}
                    .spinner {{
                        border: 4px solid #f3f3f3;
                        border-top: 4px solid #ffc107;
                        border-radius: 50%;
                        width: 30px;
                        height: 30px;
                        animation: spin 1s linear infinite;
                        margin: 0 auto 20px;
                    }}
                    @keyframes spin {{
                        0% {{ transform: rotate(0deg); }}
                        100% {{ transform: rotate(360deg); }}
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="success-icon">✓</div>
                    <h1>Payment Successful!</h1>
                    <p>Your payment has been processed successfully. Redirecting to order confirmation...</p>
                    <div class="spinner"></div>
                    <p><small>If you are not redirected automatically, <a href="/order-confirmation/{order_id}/">click here</a>.</small></p>
                </div>
                
                <script>
                    setTimeout(function() {{
                        window.location.href = '/order-confirmation/{order_id}/';
                    }}, 2000);
                </script>
            </body>
            </html>
            """
            return HttpResponse(html_content, content_type='text/html')
        
    except Exception as e:
        print(f"DEBUG: Error processing payment: {e}")
        print(f"DEBUG: Error type: {type(e).__name__}")
        
        if request.method == 'GET':
            messages.error(request, f"Payment processing error: {str(e)}")
            return redirect('checkout')
        else:
            return JsonResponse({'error': str(e)}, status=400)

@csrf_exempt
def razorpay_payment_failed(request):
    """Handle Razorpay payment failure"""
    try:
        # Handle both GET (redirect) and POST (webhook) requests
        if request.method == 'GET':
            # Handle redirect from Razorpay
            order_id = request.GET.get('order_id')
            razorpay_payment_id = request.GET.get('razorpay_payment_id')
            razorpay_order_id = request.GET.get('razorpay_order_id')
            
            # Try to find order if not provided
            if not order_id:
                try:
                    if razorpay_payment_id:
                        payment = Payment.objects.get(transaction_id__contains=razorpay_payment_id)
                        order_id = payment.order.id
                    elif razorpay_order_id:
                        payment = Payment.objects.filter(transaction_id__contains=razorpay_order_id).first()
                        if payment:
                            order_id = payment.order.id
                except:
                    pass
                    
        elif request.method == 'POST':
            # Handle webhook POST request
            order_id = request.POST.get('order_id')
        else:
            return JsonResponse({'error': 'Invalid request method'}, status=405)
        
        if order_id:
            order = Order.objects.get(id=order_id)
            order.payment_status = 'failed'
            order.status = 'pending'
            order.save()
            
            payment = Payment.objects.get(order=order)
            payment.status = 'failed'
            payment.save()
        
        messages.error(request, 'Payment failed. Please try again or choose a different payment method.')
        
        if request.method == 'GET':
            # Redirect back to checkout
            return redirect('checkout')
        else:
            # Return JSON for webhook
            return JsonResponse({
                'status': 'failed',
                'message': 'Payment failed. Please try again.',
                'redirect_url': '/checkout/'
            })
        
    except Exception as e:
        print(f"Payment failure handler error: {e}")
        
        if request.method == 'GET':
            messages.error(request, 'Payment processing failed. Please try again.')
            return redirect('checkout')
        else:
            return JsonResponse({'error': str(e)}, status=500)

RAZOR_KEY_ID = 'rzp_test_Ri3GAu0IIA4Qry'
RAZOR_KEY_SECRET = 'hf5Z2UzqiCtua4VK3EJRPzU9'

