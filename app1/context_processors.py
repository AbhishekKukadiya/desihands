from .models import cart, register, category







def cart_counter(request):







    count = 0







    if 'login' in request.session:



        try:



            user = register.objects.get(email=request.session['login'])



            count = cart.objects.filter(user=user, order_id=0).count()



        except:



            pass







    return {



        'cart_count': count



    }







def categories_context(request):



    """



    Provides categories to all templates for navigation



    """



    categories = category.objects.all()



    return {



        'navbar_categories': categories



    }