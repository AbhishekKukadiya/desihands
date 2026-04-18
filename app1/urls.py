from django.urls import path
from .views import *

urlpatterns = [

    path('',index,name='index'),

    path('store/',store,name='store'),

    path('register/',register_view,name='register'),

    path('login/',login,name='login'),

    path('logout/',logout,name='logout'),

    path('product/<int:id>/',product_page,name='product'),

    path('productdetail/<int:id>/',product_detail_view,name='productdetail'),

    path('cart/', cart_page, name='cart'),

    path('remove/<int:id>/', remove_cart, name='remove_cart'),

    path('increase/<int:id>/', increase_qty, name='increase_qty'),

    path('decrease/<int:id>/', decrease_qty, name='decrease_qty'),

    path('search/', search_product, name='search_product'),

    path('seller-register/', seller_register, name='seller_register'),

    path('seller-login/', seller_login, name='seller_login'),

    path('seller-logout/', seller_logout, name='seller_logout'),

    path('seller-dashboard/', seller_dashboard, name='seller_dashboard'),

    path('add-product/', add_product, name='add_product'),

    path('edit-product/<int:product_id>/', edit_product, name='edit_product'),

    path('delete-product/<int:product_id>/', delete_product, name='delete_product'),

    path('toggle-product/<int:product_id>/', toggle_product_status, name='toggle_product_status'),

    path('checkout/', checkout, name='checkout'),

    path('place-order/', place_order, name='place_order'),

    path('order-confirmation/<int:order_id>/', order_confirmation, name='order_confirmation'),

    path('my-orders/', my_orders, name='my_orders'),

    path('track-order/', track_order_page, name='track_order'),

    path('track-order/result/', track_order_result, name='track_order_result'),

    path('api/quick-track/', quick_track_api, name='quick_track_api'),

    path('cancel-order/<int:order_id>/', cancel_order, name='cancel_order'),

    path('manage-profile/', manage_profile, name='manage_profile'),

    path('about/', about_page, name='about'),

    # Razorpay Payment URLs
    path('razorpay/create-order/', create_razorpay_order, name='create_razorpay_order'),
    path('razorpay/payment-success/', razorpay_payment_success, name='razorpay_payment_success'),
    path('razorpay/payment-failed/', razorpay_payment_failed, name='razorpay_payment_failed'),

]