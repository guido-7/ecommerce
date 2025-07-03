# orders/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView
from django.contrib import messages
from django.db.models import Q, Prefetch
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .models import Order, OrderItem
from store.models import Product
from django.contrib.auth.mixins import UserPassesTestMixin


class StoreManagerRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.groups.filter(name='Store Manager').exists()


class OrderManagementView(StoreManagerRequiredMixin, ListView):
    model = Order
    template_name = 'store/manage.html'
    context_object_name = 'orders'
    paginate_by = 25

    def get_queryset(self):
        queryset = super().get_queryset().prefetch_related(
            Prefetch('items', queryset=OrderItem.objects.select_related('product'))
        ).select_related('user')

        # Filtro per stato
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)

        # Filtro per ricerca
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(id__icontains=search_query) |
                Q(user__username__icontains=search_query) |
                Q(user__email__icontains=search_query) |
                Q(user__first_name__icontains=search_query) |
                Q(user__last_name__icontains=search_query)
            )

        # Filtro per data
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)

        # Ordinamento
        sort_by = self.request.GET.get('sort_by', '-created_at')
        sort_order = self.request.GET.get('sort_order', 'desc')

        sort_mapping = {
            'id': 'id',
            'user': 'user__username',
            'created_at': 'created_at',
            'total_amount': 'total_amount',
            'status': 'status'
        }

        if sort_by in sort_mapping:
            order_field = sort_mapping[sort_by]
            if sort_order == 'desc' and not order_field.startswith('-'):
                order_field = f'-{order_field}'
            queryset = queryset.order_by(order_field)
        else:
            # Default: ordinamento per data di creazione (più recenti prima)
            queryset = queryset.order_by('-created_at')

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Filtri
        context['status_choices'] = Order.OrderStatus.choices
        context['current_status'] = self.request.GET.get('status', '')
        context['search_query'] = self.request.GET.get('search', '')
        context['start_date'] = self.request.GET.get('start_date', '')
        context['end_date'] = self.request.GET.get('end_date', '')

        # Ordinamento
        context['sort_by'] = self.request.GET.get('sort_by', '-created_at').lstrip('-')
        context['sort_order'] = self.request.GET.get('sort_order', 'desc')

        # Paginazione
        page = self.request.GET.get('page')
        paginator = Paginator(self.get_queryset(), self.paginate_by)

        try:
            orders = paginator.page(page)
        except PageNotAnInteger:
            orders = paginator.page(1)
        except EmptyPage:
            orders = paginator.page(paginator.num_pages)

        context['orders'] = orders

        return context


@login_required
def update_order_status(request, pk):
    """
    View to update the status of an order.
    """
    if not request.user.groups.filter(name='Store Manager').exists():
        messages.error(request, "You don't have permission to perform this action.")
        return redirect('order_history')

    order = get_object_or_404(Order, pk=pk)

    if request.method == 'POST':
        new_status = request.POST.get('status')

        if new_status and new_status in dict(Order.OrderStatus.choices):
            previous_status = order.get_status_display()
            order.status = new_status
            order.save()
            messages.success(
                request,
                f'Order #{order.id} status updated from {previous_status} to {order.get_status_display()}'
            )
        else:
            messages.error(request, 'Invalid status selected.')

        return redirect('order_management')

    return redirect('order_management')


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
            order.delete()  # Delete the empty order
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