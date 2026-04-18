from django.db import models
from django.utils import timezone

class category(models.Model):
    name=models.CharField(max_length=50)
    image=models.ImageField(upload_to='category_images')

    def __str__(self):
       return self.name

class register(models.Model):
    username = models.CharField(max_length=50, unique=True)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15)
    address = models.TextField()
    city = models.CharField(max_length=50)
    state = models.CharField(max_length=50)
    pincode = models.CharField(max_length=10)
    password = models.CharField(max_length=100)

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
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.business_name

class product(models.Model):
    name=models.CharField(max_length=50)
    price=models.FloatField()
    description=models.TextField()
    stock=models.IntegerField()
    image=models.ImageField()
    category=models.ForeignKey(category, on_delete=models.CASCADE)
    seller=models.ForeignKey(Seller, on_delete=models.CASCADE, null=True, blank=True)
    is_active=models.BooleanField(default=True)
   
    def __str__(self):
        return self.name
    
    def is_in_stock(self):
        """Check if product is in stock"""
        return self.stock > 0
    
    def stock_status(self):
        """Returns stock status text"""
        if self.stock > 0:
            return f"In Stock ({self.stock} units)"
        return "Out of Stock"

class cart(models.Model):
    name=models.ForeignKey(product, on_delete=models.CASCADE) 
    user=models.ForeignKey(register,on_delete=models.CASCADE)
    total_price=models.FloatField()
    qty=models.IntegerField()
    order_id=models.IntegerField(default=0)

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

class OrderItem(models.Model):
    order=models.ForeignKey(Order, on_delete=models.CASCADE)
    product=models.ForeignKey(product, on_delete=models.CASCADE)
    quantity=models.IntegerField()
    price=models.FloatField()
    total_price=models.FloatField()

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"
    
class Payment(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    payment_method = models.CharField(max_length=50)
    transaction_id = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20)

    def __str__(self):
        return self.transaction_id
    
class Shipping(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    courier_name = models.CharField(max_length=100)
    tracking_number = models.CharField(max_length=100, unique=True)
    shipped_date = models.DateTimeField(null=True, blank=True)
    delivery_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, default='pending')

    def __str__(self):
        return self.tracking_number