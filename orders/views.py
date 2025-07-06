from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db import transaction
from django.db.models import Q, Prefetch
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView
from .models import Order, OrderItem
from store.models import Product, PromoCode


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
        messages.error(request, "Il tuo carrello è vuoto.")
        return redirect('product_list')

    # Usa una transazione per garantire consistenza
    with transaction.atomic():
        # Calcola il subtotale usando i prezzi scontati
        subtotal = Decimal('0.00')
        cart_items = []

        # Verifica stock e calcola subtotale
        for product_id, item_data in cart.items():
            try:
                product = Product.objects.get(id=product_id)
                quantity = item_data['quantity']

                # Verifica disponibilità stock
                if product.stock < quantity:
                    messages.error(request, f"Spiacenti, {product.name} non è disponibile in quantità sufficiente.")
                    return redirect('view_cart')

                # Usa il prezzo scontato se disponibile
                actual_price = product.get_actual_price()
                item_total = actual_price * quantity
                subtotal += item_total

                cart_items.append({
                    'product': product,
                    'quantity': quantity,
                    'price': actual_price,
                    'total': item_total
                })

            except Product.DoesNotExist:
                messages.error(request, f"Prodotto non trovato.")
                return redirect('view_cart')

        # Gestisci il promo code
        promo_code = None
        promo_discount_amount = Decimal('0.00')
        applied_promo = request.session.get('applied_promo_code')

        if applied_promo:
            try:
                promo_code = PromoCode.objects.get(code=applied_promo)
                if promo_code.is_valid():
                    promo_discount_amount = subtotal * (promo_code.discount_percentage / 100)
                    # Arrotonda a 2 decimali
                    promo_discount_amount = promo_discount_amount.quantize(Decimal('0.01'))
                else:
                    # Rimuovi il promo code scaduto
                    del request.session['applied_promo_code']
                    messages.warning(request, 'Il codice promo è scaduto ed è stato rimosso.')
            except PromoCode.DoesNotExist:
                del request.session['applied_promo_code']
                messages.warning(request, 'Codice promo non valido rimosso.')

        # Calcola il totale finale
        final_total = subtotal - promo_discount_amount

        # Crea l'ordine
        order = Order.objects.create(
            user=request.user,
            total_amount=final_total,
            promo_code_used=applied_promo if promo_code else '',
            discount_amount=promo_discount_amount
        )

        # Crea gli items dell'ordine e aggiorna lo stock
        for item in cart_items:
            product = item['product']
            quantity = item['quantity']
            price = item['price']

            # Crea l'item dell'ordine
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=quantity,
                price=price
            )

            # Diminuisci lo stock
            product.stock -= quantity
            product.save()

        # Incrementa il contatore di utilizzi del promo code se applicato
        if promo_code:
            # Se hai aggiunto il campo used_count al modello PromoCode
            if hasattr(promo_code, 'used_count'):
                promo_code.used_count += 1
                promo_code.save()

        # Svuota il carrello e rimuovi il promo code dalla sessione
        del request.session['cart']
        if 'applied_promo_code' in request.session:
            del request.session['applied_promo_code']

        messages.success(request, f'Ordine completato con successo! Totale: €{final_total}')
        return redirect('order_success', order_id=order.id)


@login_required
def order_success(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    context = {
        'order': order,
        'order_items': order.items.all(),
        'subtotal': order.get_subtotal(),
        'discount_amount': order.discount_amount,
        'total_amount': order.total_amount,
        'promo_code_used': order.promo_code_used,
        'total_savings': order.get_savings(),
    }

    return render(request, 'orders/order_success.html', context)


class OrderHistoryView(LoginRequiredMixin, ListView):
    model = Order
    template_name = 'orders/order_history.html'
    context_object_name = 'orders'
    paginate_by = 10  # Opzionale: 10 ordini per pagina

    def get_queryset(self):
        """
        Restituisce gli ordini dell'utente corrente con i relativi items e prodotti
        """
        return Order.objects.filter(user=self.request.user).prefetch_related(
            'items__product'
        ).order_by('-created_at')

    def get_context_data(self, **kwargs):
        """
        Aggiunge contesto extra se necessario
        """
        context = super().get_context_data(**kwargs)

        # Puoi aggiungere dati extra al contesto se necessario
        # Ad esempio, statistiche generali sugli ordini
        context['total_orders'] = self.get_queryset().count()

        return context