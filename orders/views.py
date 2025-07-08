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
    template_name = 'dashboard/manage.html'
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


def get_suggested_address(user):
    """
    Logica per ottenere l'indirizzo suggerito:
    1. Prima controlla se l'utente ha un indirizzo nel profilo
    2. Poi controlla l'ultimo ordine dell'utente
    3. Altrimenti restituisce None

    Returns:
        tuple: (address_dict, source_string) o (None, None)
    """
    # Controllo 1: Indirizzo dal profilo utente
    if (hasattr(user, 'street_address') and
            user.street_address and
            user.city and
            user.postal_code and
            user.country):
        return {
            'street_address': user.street_address,
            'city': user.city,
            'postal_code': user.postal_code,
            'country': user.country
        }, 'user_profile'

    # Controllo 2: Ultimo ordine dell'utente
    try:
        last_order = Order.objects.filter(user=user).order_by('-id').first()
        if last_order:
            return {
                'street_address': last_order.street_address,
                'city': last_order.city,
                'postal_code': last_order.postal_code,
                'country': last_order.country
            }, 'last_order'
    except Order.DoesNotExist:
        pass

    # Controllo 3: Nessun indirizzo trovato
    return None, None


@login_required
def checkout_address(request):
    """
    Step 1: Pagina per inserire l'indirizzo di spedizione
    """
    # Verifica che il carrello non sia vuoto
    cart = request.session.get('cart', {})
    if not cart:
        messages.error(request, "Il tuo carrello è vuoto.")
        return redirect('product_list')

    user = request.user

    if request.method == 'POST':
        # Processare il form dell'indirizzo
        street_address = request.POST.get('street_address', '').strip()
        city = request.POST.get('city', '').strip()
        postal_code = request.POST.get('postal_code', '').strip()
        country = request.POST.get('country', '').strip()
        save_as_default = request.POST.get('save_as_default') == '1'

        # Validazione dei campi obbligatori
        if not all([street_address, city, postal_code, country]):
            messages.error(request, 'Please fill in all required fields.')
            return render(request, 'checkout.html', {
                'suggested_address': get_suggested_address(user)[0],
                'address_source': get_suggested_address(user)[1],
                'form_data': request.POST
            })

        # Salva l'indirizzo nella sessione per il prossimo step
        request.session['checkout_address'] = {
            'street_address': street_address,
            'city': city,
            'postal_code': postal_code,
            'country': country,
            'save_as_default': save_as_default
        }

        # Redirect al processamento dell'ordine
        return redirect('checkout_process')

    # GET request - mostrare il form dell'indirizzo
    suggested_address, address_source = get_suggested_address(user)

    context = {
        'suggested_address': suggested_address,
        'address_source': address_source,
    }

    return render(request, 'orders/checkout.html', context)


@login_required
def checkout_process(request):
    """
    Step 2: Processamento dell'ordine con l'indirizzo dalla sessione
    Questa è la tua funzione checkout esistente, modificata per usare l'indirizzo dalla sessione
    """
    from django.db import transaction
    from decimal import Decimal

    # Verifica che ci sia un indirizzo nella sessione
    checkout_address = request.session.get('checkout_address')
    if not checkout_address:
        messages.error(request, "Indirizzo di spedizione mancante.")
        return redirect('checkout_address')

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

        # Crea l'ordine CON L'INDIRIZZO DALLA SESSIONE
        order = Order.objects.create(
            user=request.user,
            total_amount=final_total,
            promo_code_used=applied_promo if promo_code else '',
            discount_amount=promo_discount_amount,
            # Aggiungi i campi dell'indirizzo
            street_address=checkout_address['street_address'],
            city=checkout_address['city'],
            postal_code=checkout_address['postal_code'],
            country=checkout_address['country'],
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

        # Salva l'indirizzo come predefinito se richiesto
        if checkout_address['save_as_default']:
            user = request.user
            user.street_address = checkout_address['street_address']
            user.city = checkout_address['city']
            user.postal_code = checkout_address['postal_code']
            user.country = checkout_address['country']
            user.save()
            messages.success(request, 'Your address has been saved as default.')

        # Svuota il carrello, rimuovi il promo code e l'indirizzo dalla sessione
        del request.session['cart']
        if 'applied_promo_code' in request.session:
            del request.session['applied_promo_code']
        if 'checkout_address' in request.session:
            del request.session['checkout_address']

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