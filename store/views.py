from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, Count, Prefetch
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.utils.text import slugify
from django.views.decorators.http import require_POST
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView

from . import models
from .models import Product, ProductImage, Category, Brand, PromoCode
from orders.models import Order, OrderItem
from .forms import CategoryForm, PromoCodeForm, BrandForm


class ProductListView(ListView):
    model = Product
    template_name = 'store/product_list.html'
    context_object_name = 'products'
    paginate_by = 8 # Show 8 products per page

    def get_queryset(self):
        queryset = super().get_queryset().order_by('-created_at')

        # Filtering by category
        category_slug = self.request.GET.get('category')
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)

        # Searching by name/description
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                models.Q(name__icontains=search_query) | 
                models.Q(description__icontains=search_query)
            )

        return queryset

    def get_context_data(self, **kwargs):
        # Pass categories to the template so we can build the filter dropdown
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        return context

class ProductDetailView(DetailView):
    model = Product
    template_name = 'store/product_detail.html'
    context_object_name = 'product'

# === CART MANAGEMENT ===

def view_cart(request):
    cart = request.session.get('cart', {})
    cart_items = []
    total_price = 0
    subtotal = 0
    total_savings = 0

    for product_id, item_data in cart.items():
        product = Product.objects.get(id=product_id)
        actual_price = product.get_actual_price()
        total_item_price = actual_price * item_data['quantity']
        if product.discounted_price:
            total_savings += (product.price - product.discounted_price) * item_data['quantity']

        cart_items.append({
            'product': product,
            'quantity': item_data['quantity'],
            'total_price': total_item_price
        })
        subtotal += total_item_price

    # Gestisci il promo code dalla sessione
    promo_code = None
    promo_discount_amount = Decimal('0.00')
    applied_promo = request.session.get('applied_promo_code')

    if applied_promo:
        try:
            promo_code = PromoCode.objects.get(code=applied_promo)
            if promo_code.is_valid():
                promo_discount_amount = subtotal * (promo_code.discount_percentage / 100)
            else:
                # Rimuovi il promo code scaduto dalla sessione
                del request.session['applied_promo_code']
                messages.warning(request, 'Il codice promo è scaduto ed è stato rimosso.')
        except PromoCode.DoesNotExist:
            del request.session['applied_promo_code']
            messages.error(request, 'Codice promo non valido.')

    total_price = subtotal - promo_discount_amount
    total_savings += promo_discount_amount

    installment_amount = total_price / 3 if total_price > 0 else 0

    # Form per il promo code
    promo_form = PromoCodeForm()

    context = {
        'cart_items': cart_items,
        'subtotal': subtotal,
        'discount_amount': promo_discount_amount,
        'total_price': total_price,
        'total_savings': total_savings,
        'installment_amount': installment_amount,
        'promo_form': promo_form,
        'applied_promo': applied_promo,
        'promo_code': promo_code,
    }

    return render(request, 'store/cart.html', context)

def add_to_cart(request, product_id):
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        product = Product.objects.get(id=product_id)

        # Get or create the cart in the session
        cart = request.session.get('cart', {})

        cart_item = cart.get(str(product_id), {'quantity': 0, 'price': str(product.price)})
        cart_item['quantity'] += quantity

        # Ensure quantity does not exceed stock
        if cart_item['quantity'] > product.stock:
            messages.error(request, f"Cannot add {quantity} of {product.name}. Only {product.stock} left in stock.")
            return redirect('product_detail', pk=product_id)

        cart[str(product_id)] = cart_item
        request.session['cart'] = cart

        messages.success(request, f"Added {quantity} x {product.name} to your cart.")
        return redirect('product_detail', pk=product_id)
    return redirect('product_list')

def remove_from_cart(request, product_id):
    cart = request.session.get('cart', {})
    if str(product_id) in cart:
        del cart[str(product_id)]
        request.session['cart'] = cart
        messages.success(request, "Item removed from cart.")
    return redirect('view_cart')


@require_POST
def apply_promo_code(request):
    form = PromoCodeForm(request.POST)

    if form.is_valid():
        code = form.cleaned_data['code'].upper()

        try:
            promo_code = PromoCode.objects.get(code=code)
            if promo_code.is_valid():
                # Salva il codice promo nella sessione
                request.session['applied_promo_code'] = code
                messages.success(request,
                                 f'Codice promo "{code}" applicato con successo! Sconto del {promo_code.discount_percentage}%')

                # Se è una richiesta AJAX, ritorna JSON
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True,
                        'message': f'Codice promo applicato! Sconto del {promo_code.discount_percentage}%',
                        'discount_percentage': float(promo_code.discount_percentage)
                    })
            else:
                messages.error(request, 'Il codice promo è scaduto o non ancora valido.')

                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'message': 'Il codice promo è scaduto o non ancora valido.'
                    })

        except PromoCode.DoesNotExist:
            messages.error(request, 'Codice promo non valido.')

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': 'Codice promo non valido.'
                })
    else:
        messages.error(request, 'Inserisci un codice promo valido.')

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': 'Inserisci un codice promo valido.'
            })

    return redirect('cart')


def remove_promo_code(request):
    if 'applied_promo_code' in request.session:
        del request.session['applied_promo_code']
        messages.success(request, 'Codice promo rimosso.')

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'message': 'Codice promo rimosso.'})

    return redirect('cart')

def update_cart_quantity(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = request.session.get('cart', {})
    product_id_str = str(product_id)

    if request.method == 'POST':
        action = request.POST.get('action')

        if product_id_str in cart:
            if action == 'increase':
                # Controlla che non si superi la disponibilità
                if cart[product_id_str]['quantity'] < product.stock:
                    cart[product_id_str]['quantity'] += 1
                else:
                    messages.error(request,
                                   f"Non è possibile aggiungere altre unità di {product.name}. Disponibilità massima raggiunta.")
            elif action == 'decrease':
                if cart[product_id_str]['quantity'] > 1:
                    cart[product_id_str]['quantity'] -= 1
                else:
                    # Se la quantità è 1 e si clicca su diminuisci, rimuovi il prodotto
                    return redirect('remove_from_cart', product_id=product_id)

            request.session['cart'] = cart
            #messages.success(request, "Carrello aggiornato")
        else:
            messages.error(request, "Prodotto non trovato nel carrello")

    return redirect('view_cart')


class StoreManagerRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.groups.filter(name='Store Manager').exists()


class ProductCreateView(StoreManagerRequiredMixin, CreateView):
    model = Product
    fields = ['category', 'name', 'brand', 'description', 'price', 'discounted_price', 'stock']
    template_name = 'store/product_form.html'
    success_url = reverse_lazy('product_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Per la creazione, non ci sono immagini esistenti
        context['existing_images'] = []
        return context

    def form_valid(self, form):
        # Validazione prezzo scontato
        if form.cleaned_data.get('discounted_price'):
            if form.cleaned_data['discounted_price'] >= form.cleaned_data['price']:
                form.add_error('discounted_price', 'Il prezzo scontato deve essere inferiore al prezzo originale.')
                return self.form_invalid(form)

        return super().form_valid(form)

    def post(self, request, *args, **kwargs):
        form = self.get_form()

        if form.is_valid():
            # Controlla che ci sia almeno una immagine
            image_files = []
            for key, file in request.FILES.items():
                if key.startswith('image_') and file:
                    image_files.append(file)

            if not image_files:
                messages.error(request, 'È richiesta almeno una immagine per il prodotto.')
                return render(request, self.template_name, {
                    'form': form,
                    'existing_images': []
                })

            # Validazione prezzo scontato
            if form.cleaned_data.get('discounted_price'):
                if form.cleaned_data['discounted_price'] >= form.cleaned_data['price']:
                    form.add_error('discounted_price', 'Il prezzo scontato deve essere inferiore al prezzo originale.')
                    return render(request, self.template_name, {
                        'form': form,
                        'existing_images': []
                    })

            # Salva il prodotto
            product = form.save()

            # Salva le immagini
            for image_file in image_files:
                ProductImage.objects.create(
                    product=product,
                    image=image_file
                )

            # Messaggio di successo con informazioni sul sconto
            success_message = f'Prodotto "{product.name}" creato con successo!'
            if product.discounted_price:
                savings = product.price - product.discounted_price
                savings_percent = (savings / product.price) * 100
                success_message += f' Sconto applicato: €{savings:.2f} ({savings_percent:.0f}%)'

            messages.success(request, success_message)
            return redirect(self.success_url)

        return render(request, self.template_name, {
            'form': form,
            'existing_images': []
        })


class ProductUpdateView(StoreManagerRequiredMixin, UpdateView):
    model = Product
    fields = ['category', 'name', 'brand', 'description', 'price', 'discounted_price', 'stock']
    template_name = 'store/product_form.html'
    success_url = reverse_lazy('product_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['existing_images'] = self.object.images.all()
        return context

    def form_valid(self, form):
        # Validazione prezzo scontato
        if form.cleaned_data.get('discounted_price'):
            if form.cleaned_data['discounted_price'] >= form.cleaned_data['price']:
                form.add_error('discounted_price', 'Il prezzo scontato deve essere inferiore al prezzo originale.')
                return self.form_invalid(form)

        return super().form_valid(form)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()

        if form.is_valid():
            # Gestione rimozione immagini esistenti
            images_to_delete = request.POST.getlist('delete_image')

            # Filtra solo i valori non vuoti
            images_to_delete = [img_id for img_id in images_to_delete if img_id]

            if images_to_delete:
                ProductImage.objects.filter(
                    id__in=images_to_delete,
                    product=self.object
                ).delete()

            # Controlla nuove immagini
            new_image_files = []
            for key, file in request.FILES.items():
                if key.startswith('image_') and file:
                    new_image_files.append(file)

            # Controlla che rimanga almeno una immagine
            remaining_images = self.object.images.exclude(id__in=images_to_delete).count()
            total_images = remaining_images + len(new_image_files)

            if total_images == 0:
                messages.error(request, 'È richiesta almeno una immagine per il prodotto.')
                return render(request, self.template_name, {
                    'form': form,
                    'existing_images': self.object.images.all()
                })

            # Validazione prezzo scontato
            if form.cleaned_data.get('discounted_price'):
                if form.cleaned_data['discounted_price'] >= form.cleaned_data['price']:
                    form.add_error('discounted_price', 'Il prezzo scontato deve essere inferiore al prezzo originale.')
                    return render(request, self.template_name, {
                        'form': form,
                        'existing_images': self.object.images.all()
                    })

            # Salva il prodotto
            product = form.save()

            # Salva le nuove immagini
            for image_file in new_image_files:
                ProductImage.objects.create(
                    product=product,
                    image=image_file
                )

            # Messaggio di successo con informazioni sul sconto
            success_message = f'Prodotto "{product.name}" aggiornato con successo!'
            if product.discounted_price:
                savings = product.price - product.discounted_price
                savings_percent = (savings / product.price) * 100
                success_message += f' Sconto applicato: €{savings:.2f} ({savings_percent:.0f}%)'
            elif hasattr(self.object, '_original_discounted_price') and self.object._original_discounted_price:
                success_message += ' Sconto rimosso.'

            messages.success(request, success_message)
            return redirect(self.success_url)

        return render(request, self.template_name, {
            'form': form,
            'existing_images': self.object.images.all()
        })

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        # Memorizza il valore originale per confronto
        obj._original_discounted_price = obj.discounted_price
        return obj


class ProductDeleteView(StoreManagerRequiredMixin, DeleteView):
    """
    View to delete a product with a confirmation step.
    """
    model = Product
    template_name = 'dashboard/confirm_delete.html'
    success_url = reverse_lazy('manage')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Conferma Eliminazione Prodotto'
        context['object_name'] = self.object.name
        context['cancel_url'] = reverse_lazy('manage')
        return context

    def form_valid(self, form):
        messages.success(self.request, f'Prodotto "{self.object.name}" eliminato con successo.')
        return super().form_valid(form)


class ManageView(StoreManagerRequiredMixin, ListView):
    """
    Main management page with product, category, and order lists.
    Inherits from ListView to handle pagination and filtering.
    """
    model = Product
    template_name = 'dashboard/manage.html'
    context_object_name = 'products'
    paginate_by = 10

    def get_queryset(self):
        """
        Handles filtering, searching, and sorting for the product list.
        """
        queryset = super().get_queryset().annotate(image_count=Count('images'))

        # Filtering by category
        category_id = self.request.GET.get('category')
        if category_id:
            queryset = queryset.filter(category__id=category_id)

        # Filtering by brand
        brand_id = self.request.GET.get('brand')
        if brand_id:
            queryset = queryset.filter(brand__id=brand_id)

        # Searching by name
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(name__icontains=search_query)

        sort_by = self.request.GET.get('sort_by', 'created_at')
        sort_order = self.request.GET.get('sort_order', 'desc')

        # Mappatura dei campi ordinabili per prodotti
        product_sort_mapping = {
            'id': 'id',
            'name': 'name',
            'category': 'category__name',
            'price': 'price',
            'stock': 'stock',
            'image_count': 'image_count',
            'created_at': 'created_at'
        }

        # Applica ordinamento
        if sort_by in product_sort_mapping:
            order_field = product_sort_mapping[sort_by]
            if sort_order == 'desc':
                order_field = f'-{order_field}'
            queryset = queryset.order_by(order_field)
        else:
            # Default: ordinamento per data di creazione (più recenti prima)
            queryset = queryset.order_by('-created_at')

        return queryset

    def get_context_data(self, **kwargs):
        """
        Adds categories, orders, and other necessary data to the template context.
        """
        context = super().get_context_data(**kwargs)
        context['all_categories'] = Category.objects.all().order_by('name')  # For the filter dropdown
        context['all_brands'] = Brand.objects.all().order_by('name')  # For the filter dropdown

        # === Gestione categorie ===
        category_search_query = self.request.GET.get('category_search')
        category_sort_by = self.request.GET.get('category_sort_by', 'name')
        category_sort_order = self.request.GET.get('category_sort_order', 'asc')

        categories_qs = Category.objects.all()

        # Filtro di ricerca per categorie
        if category_search_query:
            categories_qs = categories_qs.filter(name__icontains=category_search_query)

        # Mappatura dei campi ordinabili per categorie
        category_sort_mapping = {
            'id': 'id',
            'name': 'name',
            'slug': 'slug'
        }

        # Sorting by categories
        if category_sort_by in category_sort_mapping:
            order_field = category_sort_mapping[category_sort_by]
            if category_sort_order == 'desc':
                order_field = f'-{order_field}'
            categories_qs = categories_qs.order_by(order_field)
        else:
            # Default: sorting by name (ascending)
            categories_qs = categories_qs.order_by('name')

        context['categories'] = categories_qs

        # === Gestione Brand ===

        brand_search_query = self.request.GET.get('brand_search', '')
        brand_sort_by = self.request.GET.get('brand_sort_by', 'name')
        brand_sort_order = self.request.GET.get('brand_sort_order', 'asc')

        brands_qs = Brand.objects.annotate(product_count=Count('products'))

        # Filtro di ricerca per brand
        if brand_search_query:
            brands_qs = brands_qs.filter(name__icontains=brand_search_query)

        # Mappatura dei campi ordinabili per brand
        brand_sort_mapping = {
            'id': 'id',
            'name': 'name',
            'slug': 'slug',
            'product_count': 'product_count'
        }

        # Ordinamento brand
        if brand_sort_by in brand_sort_mapping:
            order_field = brand_sort_mapping[brand_sort_by]
            if brand_sort_order == 'desc':
                order_field = f'-{order_field}'
            brands_qs = brands_qs.order_by(order_field)
        else:
            # Default: ordinamento per nome (ascendente)
            brands_qs = brands_qs.order_by('name')

        # Paginazione per brand
        brand_page = self.request.GET.get('brand_page', 1)
        brand_paginator = Paginator(brands_qs, 10)  # 10 brand per pagina

        try:
            brands = brand_paginator.page(brand_page)
        except PageNotAnInteger:
            brands = brand_paginator.page(1)
        except EmptyPage:
            brands = brand_paginator.page(brand_paginator.num_pages)

        context['brands'] = brands
        context['brand_search_query'] = brand_search_query
        context['brand_sort_by'] = brand_sort_by
        context['brand_sort_order'] = brand_sort_order

        # === Gestione ordini ===
        order_search_query = self.request.GET.get('order_search', '')
        current_order_status = self.request.GET.get('status', '')
        order_sort_by = self.request.GET.get('order_sort_by', '-created_at')
        order_sort_order = self.request.GET.get('order_sort_order', 'desc')
        items_per_page = int(self.request.GET.get('items_per_page', 25))
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')

        # Filtro stato ordine
        orders_qs = Order.objects.all().prefetch_related(
            Prefetch('items', queryset=OrderItem.objects.select_related('product')))

        if current_order_status:
            orders_qs = orders_qs.filter(status=current_order_status)

        # Filtro ricerca ordine
        if order_search_query:
            orders_qs = orders_qs.filter(
                Q(id__icontains=order_search_query) |
                Q(user__username__icontains=order_search_query) |
                Q(user__email__icontains=order_search_query) |
                Q(user__first_name__icontains=order_search_query) |
                Q(user__last_name__icontains=order_search_query)
            )

        # Filtro data ordine
        if start_date:
            orders_qs = orders_qs.filter(created_at__gte=start_date)
        if end_date:
            orders_qs = orders_qs.filter(created_at__lte=end_date)

        # Ordinamento ordini
        order_sort_mapping = {
            'id': 'id',
            'user': 'user__username',
            'created_at': 'created_at',
            'total_amount': 'total_amount',
            'status': 'status'
        }

        # Rimuovi eventuali '-' iniziali per il mapping
        clean_order_sort_by = order_sort_by.lstrip('-')
        if clean_order_sort_by in order_sort_mapping:
            order_field = order_sort_mapping[clean_order_sort_by]
        if order_sort_order == 'desc' and not order_sort_by.startswith('-'):
            order_field = f'-{order_field}'
        elif order_sort_order == 'asc' and order_sort_by.startswith('-'):
            order_field = order_field.lstrip('-')
            orders_qs = orders_qs.order_by(order_field)
        else:
            # Default: ordinamento per data di creazione (più recenti prima)
            orders_qs = orders_qs.order_by('-created_at')

        # Paginazione ordini
        order_page = self.request.GET.get('order_page', 1)
        paginator = Paginator(orders_qs, items_per_page)

        try:
            orders = paginator.page(order_page)
        except PageNotAnInteger:
            orders = paginator.page(1)
        except EmptyPage:
            orders = paginator.page(paginator.num_pages)

        context['orders'] = orders
        context['status_choices'] = Order.OrderStatus.choices
        context['order_search_query'] = order_search_query
        context['current_order_status'] = current_order_status
        context['order_sort_by'] = clean_order_sort_by
        context['order_sort_order'] = order_sort_order
        context['items_per_page'] = items_per_page
        context['start_date'] = start_date
        context['end_date'] = end_date

        # Filter for orders
        context['current_category_filter'] = self.request.GET.get('category', '')
        context['current_brand_filter'] = self.request.GET.get('brand', '')

        context['current_search'] = self.request.GET.get('search', '')
        context['current_sort_by'] = self.request.GET.get('sort_by', 'created_at')
        context['current_sort_order'] = self.request.GET.get('sort_order', 'desc')

        context['current_category_search'] = self.request.GET.get('category_search', '')
        context['current_category_sort_by'] = self.request.GET.get('category_sort_by', 'name')
        context['current_category_sort_order'] = self.request.GET.get('category_sort_order', 'asc')

        context['current_brand_search'] = self.request.GET.get('brand_search', '')
        context['current_brand_sort_by'] = self.request.GET.get('brand_sort_by', 'name')
        context['current_brand_sort_order'] = self.request.GET.get('brand_sort_order', 'asc')

        context['active_tab'] = self.request.GET.get('tab', 'products')

        return context

# === CATEGORY MANAGEMENT ===

class CategoryCreateView(StoreManagerRequiredMixin, CreateView):
    """
    View to create a new category.
    """
    model = Category
    form_class = CategoryForm
    template_name = 'dashboard/category_form.html'
    success_url = reverse_lazy('manage')

    def form_valid(self, form):
        """
        Automatically generates the slug from the category name before saving.
        """
        category = form.save(commit=False)
        category.slug = slugify(category.name)
        category.save()
        messages.success(self.request, f'Categoria "{category.name}" creata con successo!')
        return redirect(self.success_url)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Add New Category'
        context['type'] = 'Category'
        return context

class CategoryUpdateView(StoreManagerRequiredMixin, UpdateView):
    """
    View to update an existing category.
    """
    model = Category
    form_class = CategoryForm
    template_name = 'dashboard/category_form.html'
    success_url = reverse_lazy('manage')

    def form_valid(self, form):
        """
        Updates the slug if the name changes.
        """
        category = form.save(commit=False)
        category.slug = slugify(category.name)
        category.save()
        messages.success(self.request, f'Categoria "{category.name}" aggiornata con successo!')
        return redirect(self.success_url)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Update Category: {self.object.name}'
        context['type'] = 'Category'
        return context

class CategoryDeleteView(StoreManagerRequiredMixin, DeleteView):
    """
    View to delete a category with a confirmation step.
    """
    model = Category
    template_name = 'dashboard/confirm_delete.html'
    success_url = reverse_lazy('manage')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Conferma Eliminazione Categoria'
        context['object_name'] = self.object.name
        context['cancel_url'] = reverse_lazy('manage')
        return context

    def form_valid(self, form):
        messages.success(self.request, f'Categoria "{self.object.name}" eliminata con successo.')
        return super().form_valid(form)

# === BRAND MANAGEMENT ===
class BrandCreateView(StoreManagerRequiredMixin, CreateView):
    model = Brand
    form_class = BrandForm
    template_name = 'dashboard/category_form.html'
    success_url = reverse_lazy('manage')

    def form_valid(self, form):
        brand = form.save(commit=False)
        brand.slug = slugify(brand.name)
        brand.save()
        messages.success(self.request, f'Brand "{brand.name}" creato con successo!')
        return redirect(self.success_url)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Add new Brand'
        context['type'] = 'Brand'
        return context

class BrandUpdateView(StoreManagerRequiredMixin, UpdateView):
    model = Brand
    form_class = BrandForm
    template_name = 'dashboard/category_form.html'
    success_url = reverse_lazy('manage')

    def form_valid(self, form):
        brand = form.save(commit=False)
        # Se il nome è cambiato, rigenera lo slug
        if 'name' in form.changed_data:
            brand.slug = slugify(brand.name)
        brand.save()
        messages.success(self.request, f'Brand "{brand.name}" aggiornato con successo!')
        return redirect(self.success_url)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Update Brand: {self.object.name}'
        context['type'] = 'Brand'
        return context

class BrandDeleteView(StoreManagerRequiredMixin, DeleteView):
    model = Brand
    template_name = 'dashboard/confirm_delete.html'
    success_url = reverse_lazy('manage')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Conferma Eliminazione Brand'
        context['object_name'] = self.object.name
        context['cancel_url'] = reverse_lazy('manage') + '?tab=brands'
        return context

    def form_valid(self, form):
        messages.success(self.request, f'Brand "{self.object.name}" eliminato con successo.')
        return super().form_valid(form)


def update_order_status(request, pk):
    """
    View to update the status of an order.
    """
    if not request.user.groups.filter(name='Store Manager').exists():
        messages.error(request, "You don't have permission to perform this action.")
        return redirect('manage')

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

        # Mantieni i parametri della tab attiva
        tab = request.GET.get('tab', 'orders')
        page = request.GET.get('order_page', 1)
        return redirect(f'{reverse("manage")}?tab={tab}&order_page={page}')

    return redirect('manage')