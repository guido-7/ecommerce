from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView
from django.contrib import messages
from .models import Order, OrderItem
from store.models import Product

@login_required
def checkout(request):
    cart = request.session.get('cart', {})
    if not cart:
        messages.error(request, "Your cart is empty.")
        return redirect('product_list')

    # Create the order
    order = Order.objects.create(user=request.user, total_amount=0)

    total_amount = 0
    for product_id, item_data in cart.items():
        product = Product.objects.get(id=product_id)
        quantity = item_data['quantity']

        # Check stock again before finalizing
        if product.stock < quantity:
            messages.error(request, f"Sorry, {product.name} is out of stock.")
            order.delete() # Delete the empty order
            return redirect('view_cart')

        price = product.price
        total_amount += price * quantity

        # Create order item
        OrderItem.objects.create(order=order, product=product, quantity=quantity, price=price)

        # Decrease product stock
        product.stock -= quantity
        product.save()

    order.total_amount = total_amount
    order.save()

    # Clear the cart from the session
    del request.session['cart']

    return redirect('order_success', order_id=order.id)

def order_success(request, order_id):
    order = Order.objects.get(id=order_id, user=request.user)
    return render(request, 'orders/order_success.html', {'order': order})

class OrderHistoryView(ListView):
    model = Order
    template_name = 'orders/order_history.html'
    context_object_name = 'orders'

    def get_queryset(self):
        # Return orders for the current user only
        return Order.objects.filter(user=self.request.user).order_by('-created_at')