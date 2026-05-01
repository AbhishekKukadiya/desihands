import razorpay
import json
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.shortcuts import redirect, render
from .models import Order, Payment, OrderItem
from django.contrib import messages
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

class PaymentService:
    def __init__(self):
        self.client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    
    def create_order(self, amount, currency='INR'):
        """Create Razorpay order"""
        try:
            order_data = {
                'amount': amount * 100,  # Razorpay expects amount in paise
                'currency': currency,
                'payment_capture': '1'
            }
            razorpay_order = self.client.order.create(data=order_data)
            return razorpay_order
        except Exception as e:
            logger.error(f"Error creating Razorpay order: {e}")
            return None
    
    def verify_payment(self, razorpay_order_id, razorpay_payment_id, razorpay_signature):
        """Verify Razorpay payment signature"""
        try:
            params_dict = {
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': razorpay_payment_id,
                'razorpay_signature': razorpay_signature
            }
            self.client.utility.verify_payment_signature(params_dict)
            return True
        except Exception as e:
            logger.error(f"Payment verification failed: {e}")
            return False

# Initialize payment service
payment_service = PaymentService()

def initiate_payment(request, order_id):
    """Initiate payment process"""
    if 'login' not in request.session:
        return redirect('login')
    
    try:
        from .models import register
        user = register.objects.get(email=request.session['login'])
        order = Order.objects.get(id=order_id, user=user)
        
        if order.payment_status == 'paid':
            messages.info(request, "This order is already paid.")
            return redirect('order_confirmation', order_id=order.id)
        
        # Check if fallback mode is enabled or Razorpay keys are not configured
        from django.conf import settings
        if (getattr(settings, 'USE_FALLBACK_PAYMENT', False) or 
            settings.RAZORPAY_KEY_ID == 'rzp_test_YOUR_KEY_ID_HERE'):
            
            # Fallback mode: simulate successful payment
            messages.info(request, "Payment simulation: Order confirmed successfully!")
            order.payment_status = 'paid'
            order.status = 'confirmed'
            order.save()
            
            # Update payment record
            payment = Payment.objects.get(order=order)
            payment.status = 'completed'
            payment.transaction_id = f"SIMULATED-{order.id}-{timezone.now().strftime('%Y%m%d%H%M%S')}"
            payment.save()
            
            return redirect('order_confirmation', order_id=order.id)
        
        # Try to create Razorpay order
        razorpay_order = payment_service.create_order(float(order.total_amount))
        
        if not razorpay_order:
            messages.error(request, "Failed to initiate payment. Please try again.")
            return redirect('checkout')
        
        context = {
            'order': order,
            'razorpay_order_id': razorpay_order['id'],
            'razorpay_key_id': settings.RAZORPAY_KEY_ID,
            'razorpay_amount': razorpay_order['amount'],
            'currency': razorpay_order['currency'],
            'callback_url': request.build_absolute_uri('/payment/callback/'),
            'user': {
                'name': user.username,
                'email': user.email,
                'contact': user.phone
            }
        }
        
        return render(request, 'payment.html', context)
        
    except Exception as e:
        logger.error(f"Payment initiation error: {e}")
        messages.error(request, "Payment initiation failed. Please try again.")
        return redirect('checkout')

@csrf_exempt
def payment_callback(request):
    """Handle payment callback from Razorpay"""
    if request.method == 'POST':
        try:
            # Get payment details from request
            razorpay_order_id = request.POST.get('razorpay_order_id')
            razorpay_payment_id = request.POST.get('razorpay_payment_id')
            razorpay_signature = request.POST.get('razorpay_signature')
            
            # Verify payment signature
            if payment_service.verify_payment(razorpay_order_id, razorpay_payment_id, razorpay_signature):
                # Get order from Razorpay order ID
                # The Razorpay order ID contains our custom order info
                try:
                    # Find the payment record by transaction_id or razorpay_order_id
                    payment = Payment.objects.get(transaction_id__contains=razorpay_order_id)
                    order = payment.order
                except Payment.DoesNotExist:
                    # Alternative: try to find order directly if the transaction_id format is different
                    return JsonResponse({'status': 'failed', 'message': 'Order not found'})
                
                # Update payment status
                order.payment_status = 'paid'
                order.status = 'confirmed'
                order.save()
                
                # Update payment record
                payment = Payment.objects.get(order=order)
                payment.status = 'completed'
                payment.transaction_id = f"RAZOR-{razorpay_payment_id}"
                payment.save()
                
                return JsonResponse({
                    'status': 'success',
                    'order_id': order.id,
                    'redirect_url': f'/order-confirmation/{order.id}/'
                })
            else:
                return JsonResponse({'status': 'failed', 'message': 'Payment verification failed'})
                
        except Exception as e:
            logger.error(f"Payment callback error: {e}")
            return JsonResponse({'status': 'failed', 'message': 'Payment processing failed'})
    
    return JsonResponse({'status': 'failed', 'message': 'Invalid request method'})

def payment_failed(request):
    """Handle payment failure"""
    messages.error(request, "Payment failed. Please try again or choose a different payment method.")
    return redirect('checkout')

def wallet_payment(request, order_id):
    """Handle wallet payments (placeholder for future integration)"""
    if 'login' not in request.session:
        return redirect('login')
    
    try:
        from .models import register
        user = register.objects.get(email=request.session['login'])
        order = Order.objects.get(id=order_id, user=user)
        
        # For now, just mark as paid (in real implementation, integrate with Paytm/PhonePe)
        order.payment_status = 'paid'
        order.status = 'confirmed'
        order.save()
        
        payment = Payment.objects.get(order=order)
        payment.status = 'completed'
        payment.transaction_id = f"WALLET-{order.id}-{timezone.now().strftime('%Y%m%d%H%M%S')}"
        payment.save()
        
        messages.success(request, f"Order placed successfully! Order ID: #{order.id}. Wallet payment processed.")
        return redirect('order_confirmation', order_id=order.id)
        
    except Exception as e:
        logger.error(f"Wallet payment error: {e}")
        messages.error(request, "Wallet payment failed. Please try again.")
        return redirect('checkout')
