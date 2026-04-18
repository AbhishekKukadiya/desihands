from django.contrib import admin
from.models import *



class category_(admin.ModelAdmin):
    list_display=['id','name','image']

admin.site.register(category,category_)

class register_(admin.ModelAdmin):
    list_display = (
        'username',
        'email',
        'phone',
        'address',
        'city',
        'state',
        'pincode',
        'password'
    )


admin.site.register(register,register_)

class product_(admin.ModelAdmin):
    list_display=['id','name','price','description','stock','category']

admin.site.register(product,product_)

class cart_(admin.ModelAdmin):
    list_display=['id','name','user','total_price','qty','order_id']

admin.site.register(cart,cart_)

class SellerAdmin(admin.ModelAdmin):
    list_display = (
        'username',
        'email',
        'phone',
        'business_name',
        'city',
        'state',
        'is_approved',
        'created_at'
    )
    list_filter = ('is_approved', 'state', 'created_at')
    search_fields = ('username', 'email', 'business_name')
    list_editable = ('is_approved',)
    ordering = ('-created_at',)

admin.site.register(Seller, SellerAdmin)

class PaymentAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'order',
        'payment_method',
        'transaction_id',
        'amount',
        'status',
        'payment_date'
    ]

    search_fields = ['transaction_id', 'order__id']
    list_filter = ['payment_method', 'status', 'payment_date']
    ordering = ['-payment_date']


admin.site.register(Payment, PaymentAdmin)


class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'user',
        'total_amount',
        'status',
        'payment_status',
        'order_date',
        'shipping_address',
        'city',
        'state',
        'pincode',
        'phone',
        'email'
    ]
    search_fields = ['id', 'user__username', 'user__email', 'shipping_address']
    list_filter = ['status', 'payment_status', 'order_date']
    ordering = ['-order_date']
    readonly_fields = ['order_date']

admin.site.register(Order, OrderAdmin)


class OrderItemAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'order',
        'product',
        'quantity',
        'price',
        'total_price'
    ]
    search_fields = ['order__id', 'product__name']
    list_filter = ['order__order_date', 'product']
    ordering = ['-id']
    readonly_fields = ['id']

admin.site.register(OrderItem, OrderItemAdmin)


class ShippingAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'order',
        'courier_name',
        'tracking_number',
        'shipped_date',
        'delivery_date'
    ]

    search_fields = ['tracking_number', 'courier_name']
    list_filter = ['courier_name', 'shipped_date']
    ordering = ['-shipped_date']


admin.site.register(Shipping, ShippingAdmin)