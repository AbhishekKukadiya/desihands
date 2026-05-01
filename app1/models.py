from django.db import models
from django.utils import timezone

class category(models.Model):
    name=models.CharField(max_length=50)
    image=models.ImageField(upload_to='category_images')

    def __str__(self):
       return self.name
    
    def get_product_count(self):
        """Get the number of products in this category"""
        return self.product_set.count()
    
    def get_active_products(self):
        """Get only active products in this category"""
        return self.product_set.filter(is_active=True)
    
    def get_total_stock(self):
        """Get total stock of all products in this category"""
        return self.product_set.aggregate(total_stock=models.Sum('stock'))['total_stock'] or 0

class register(models.Model):
    username = models.CharField(max_length=50, unique=True)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=10)
    address = models.TextField()
    city = models.CharField(max_length=50)
    state = models.CharField(max_length=50)
    pincode = models.CharField(max_length=10)
    password = models.CharField(max_length=100)
    
    def __str__(self):
        return self.username
    
    def get_full_address(self):
        """Get the complete address"""
        return f"{self.address}, {self.city}, {self.state} - {self.pincode}"
    
    def get_order_count(self):
        """Get the number of orders placed by this user"""
        return self.order_set.count()
    
    def get_total_spent(self):
        """Get total amount spent by this user"""
        return self.order_set.filter(payment_status='paid').aggregate(
            total=models.Sum('total_amount')
        )['total'] or 0
    
    def get_cart_items_count(self):
        """Get the number of items in user's cart"""
        return self.cart_set.filter(order_id=0).count()
    
    def get_cart_total(self):
        """Get total cart amount"""
        return self.cart_set.filter(order_id=0).aggregate(
            total=models.Sum('total_price')
        )['total'] or 0

class Seller(models.Model):
    username = models.CharField(max_length=50, unique=True)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15)
    business_name = models.CharField(max_length=100)
    business_address = models.TextField()
    city = models.CharField(max_length=50)
    state = models.CharField(max_length=50)
    pincode = models.CharField(max_length=10)
    password = models.CharField(max_length=100)
    is_approved = models.BooleanField(default=False)
    
    def __str__(self):
        return self.business_name
    
    def get_full_business_address(self):
        """Get the complete business address"""
        return f"{self.business_address}, {self.city}, {self.state} - {self.pincode}"
    
    def get_product_count(self):
        """Get the number of products by this seller"""
        return self.product_set.count()
    
    def get_active_products(self):
        """Get only active products by this seller"""
        return self.product_set.filter(is_active=True)
    
    def get_total_revenue(self):
        """Get total revenue from all sold products"""
        from django.db.models import Sum
        return OrderItem.objects.filter(
            product__seller=self,
            order__payment_status='paid'
        ).aggregate(total=Sum('total_price'))['total'] or 0
    
    def get_order_count(self):
        """Get the number of orders for this seller's products"""
        return OrderItem.objects.filter(product__seller=self).values('order').distinct().count()
    
    def approval_status(self):
        """Get approval status as readable text"""
        return "Approved" if self.is_approved else "Pending Approval"

class product(models.Model):
    name=models.CharField(max_length=50)
    price=models.FloatField()
    description=models.TextField()
    stock=models.IntegerField()
    image=models.ImageField(upload_to='product_images')
    category=models.ForeignKey(category, on_delete=models.CASCADE)
    seller=models.ForeignKey(Seller, on_delete=models.CASCADE, null=True, blank=True)
    is_active=models.BooleanField(default=True)
    updated_at=models.DateTimeField(auto_now=True)
   
    def __str__(self):
        return self.name
    
    def is_in_stock(self):
        """Check if product is in stock"""
        return self.stock > 0
    
    def stock_status(self):
        """Returns stock status text"""
        if self.stock > 0:
            if self.stock <= 5:
                return f"Low Stock ({self.stock} units)"
            return f"In Stock ({self.stock} units)"
        return "Out of Stock"
    
    def get_discount_percentage(self, original_price):
        """Calculate discount percentage"""
        if original_price > self.price:
            discount = ((original_price - self.price) / original_price) * 100
            return round(discount, 2)
        return 0
    
    def get_first_letter(self):
        """Get first letter for avatar"""
        return self.name[0].upper() if self.name else 'P'
    
    def get_short_description(self, length=100):
        """Get shortened description"""
        if len(self.description) > length:
            return self.description[:length] + '...'
        return self.description
    
    def is_on_sale(self):
        """Check if product is on sale (you can customize this logic)"""
        return False  # Add your sale logic here
    
    def get_total_sold(self):
        """Get total quantity sold"""
        from django.db.models import Sum
        return OrderItem.objects.filter(product=self).aggregate(
            total=Sum('quantity')
        )['total'] or 0
    
    def get_revenue(self):
        """Get total revenue from this product"""
        from django.db.models import Sum
        return OrderItem.objects.filter(
            product=self,
            order__payment_status='paid'
        ).aggregate(total=Sum('total_price'))['total'] or 0

class cart(models.Model):
    name=models.ForeignKey(product, on_delete=models.CASCADE) 
    user=models.ForeignKey(register,on_delete=models.CASCADE)
    total_price=models.FloatField()
    qty=models.IntegerField()
    order_id=models.IntegerField(default=0)
    
    def __str__(self):
        return f"{self.user.username} - {self.name.name} ({self.qty})"
    
    def get_total_price(self):
        """Calculate total price for this cart item"""
        return self.name.price * self.qty
    
    def update_total_price(self):
        """Update total price based on current product price and quantity"""
        self.total_price = self.get_total_price()
        self.save()
    
    def is_active_cart_item(self):
        """Check if this is an active cart item (not part of an order)"""
        return self.order_id == 0

class Order(models.Model):
    user=models.ForeignKey(register, on_delete=models.CASCADE)
    total_amount=models.FloatField()
    shipping_address=models.TextField()
    city=models.CharField(max_length=50)
    state=models.CharField(max_length=50)
    pincode=models.CharField(max_length=10)
    phone=models.CharField(max_length=15)
    email=models.EmailField()
    order_date=models.DateTimeField(auto_now_add=True)
    status=models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled')
    ], default='pending')
    payment_status=models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed')
    ], default='pending')
    
    def __str__(self):
        return f"Order #{self.id} - {self.user.username}"
    
    def get_order_number(self):
        """Generate formatted order number"""
        return f"ORD-{self.id:06d}"
    
    def get_full_shipping_address(self):
        """Get complete shipping address"""
        return f"{self.shipping_address}, {self.city}, {self.state} - {self.pincode}"
    
    def get_items_count(self):
        """Get total number of items in this order"""
        return self.orderitem_set.aggregate(
            total=models.Sum('quantity')
        )['total'] or 0
    
    def get_items(self):
        """Get all order items"""
        return self.orderitem_set.all()
    
    def is_paid(self):
        """Check if order is paid"""
        return self.payment_status == 'paid'
    
    def is_delivered(self):
        """Check if order is delivered"""
        return self.status == 'delivered'
    
    def is_cancelled(self):
        """Check if order is cancelled"""
        return self.status == 'cancelled'
    
    def can_be_cancelled(self):
        """Check if order can be cancelled"""
        return self.status in ['pending', 'confirmed'] and not self.is_paid()
    
    def get_payment(self):
        """Get payment record for this order"""
        try:
            return self.payment
        except Payment.DoesNotExist:
            return None
    
    def get_shipping(self):
        """Get shipping record for this order"""
        try:
            return self.shipping
        except Shipping.DoesNotExist:
            return None
    
    def get_status_color(self):
        """Get color for status badge"""
        colors = {
            'pending': 'warning',
            'confirmed': 'info',
            'shipped': 'primary',
            'delivered': 'success',
            'cancelled': 'danger'
        }
        return colors.get(self.status, 'secondary')

class OrderItem(models.Model):
    order=models.ForeignKey(Order, on_delete=models.CASCADE)
    product=models.ForeignKey(product, on_delete=models.CASCADE)
    quantity=models.IntegerField()
    price=models.FloatField()
    total_price=models.FloatField()

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"
    
    def get_item_total(self):
        """Calculate item total price"""
        return self.quantity * self.price
    
    def update_total_price(self):
        """Update total price based on quantity and price"""
        self.total_price = self.get_item_total()
        self.save()
    
    def is_product_available(self):
        """Check if product is still available"""
        return self.product.is_active and self.product.stock >= self.quantity
    
class Payment(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    payment_method = models.CharField(max_length=50)
    transaction_id = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed')
    ], default='pending')

    def __str__(self):
        return self.transaction_id
    
    def is_successful(self):
        """Check if payment was successful"""
        return self.status == 'paid'
    
    def is_pending(self):
        """Check if payment is pending"""
        return self.status == 'pending'
    
    def is_failed(self):
        """Check if payment failed"""
        return self.status == 'failed'
    
    def get_status_color(self):
        """Get color for status badge"""
        colors = {
            'pending': 'warning',
            'paid': 'success',
            'failed': 'danger'
        }
        return colors.get(self.status, 'secondary')
    
    def get_formatted_amount(self):
        """Get formatted amount with currency"""
        return f"Rs. {self.amount}"
    
class Shipping(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    courier_name = models.CharField(max_length=100)
    tracking_number = models.CharField(max_length=100, unique=True)
    shipped_date = models.DateTimeField(null=True, blank=True)
    delivery_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('shipped', 'Shipped'),
        ('in_transit', 'In Transit'),
        ('delivered', 'Delivered'),
        ('returned', 'Returned')
    ], default='pending')

    def __str__(self):
        return self.tracking_number
    
    def is_shipped(self):
        """Check if order has been shipped"""
        return self.shipped_date is not None
    
    def is_delivered(self):
        """Check if order has been delivered"""
        return self.status == 'delivered'
    
    def get_tracking_url(self):
        """Generate tracking URL (you can customize this for different couriers)"""
        # This is a placeholder - implement actual tracking URLs for different couriers
        courier_urls = {
            'fedex': 'https://www.fedex.com/tracking?tracknumbers=',
            'dhl': 'https://www.dhl.com/en/express/tracking.html?AWB=',
            'bluedart': 'https://www.bluedart.com/tracking?track=',
        }
        courier_key = self.courier_name.lower()
        base_url = courier_urls.get(courier_key, 'https://example.com/track?tracking=')
        return f"{base_url}{self.tracking_number}"
    
    def get_delivery_days(self):
        """Calculate days taken for delivery"""
        if self.shipped_date and self.delivery_date:
            return (self.delivery_date - self.shipped_date).days
        return None
    
    def get_status_color(self):
        """Get color for status badge"""
        colors = {
            'pending': 'warning',
            'shipped': 'info',
            'in_transit': 'primary',
            'delivered': 'success',
            'returned': 'danger'
        }
        return colors.get(self.status, 'secondary')