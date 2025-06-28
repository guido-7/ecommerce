from django.shortcuts import redirect, render
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.forms.models import inlineformset_factory
from .models import Product, Category, ProductImage



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

def view_cart(request):
    cart = request.session.get('cart', {})
    cart_items = []
    total_price = 0

    for product_id, item_data in cart.items():
        product = Product.objects.get(id=product_id)
        total_item_price = product.price * item_data['quantity']
        cart_items.append({
            'product': product,
            'quantity': item_data['quantity'],
            'total_price': total_item_price
        })
        total_price += total_item_price

    return render(request, 'store/cart.html', {'cart_items': cart_items, 'total_price': total_price})

def remove_from_cart(request, product_id):
    cart = request.session.get('cart', {})
    if str(product_id) in cart:
        del cart[str(product_id)]
        request.session['cart'] = cart
        messages.success(request, "Item removed from cart.")
    return redirect('view_cart')

class StoreManagerRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.groups.filter(name='Store Manager').exists()

class ProductCreateView(StoreManagerRequiredMixin, CreateView):
    model = Product
    fields = ['category', 'name', 'description', 'price', 'stock']
    template_name = 'store/product_form.html'
    success_url = reverse_lazy('product_list')

    # Creo l’inline formset per ProductImage
    ImageFormSet = inlineformset_factory(
        Product,
        ProductImage,
        fields=['image'],
        extra=3,          # quante righe vuote
        can_delete=True   # possibilità di eliminare
    )

    def get(self, request, *args, **kwargs):
        # form principale + formset immagini
        form = self.get_form()
        formset = self.ImageFormSet()
        return render(request, self.template_name, {'form': form, 'formset': formset})

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        formset = self.ImageFormSet(request.POST, request.FILES)
        if form.is_valid() and formset.is_valid():
            # salvo il prodotto
            product = form.save()
            # associo il formset al prodotto appena creato
            formset.instance = product
            formset.save()
            return redirect(self.success_url)
        # se c’è un errore, ricarico template con form e formset validati
        return render(request, self.template_name, {'form': form, 'formset': formset})

class ProductUpdateView(StoreManagerRequiredMixin, UpdateView):
    model = Product
    fields = ['category', 'name', 'description', 'price', 'stock', 'image']
    template_name = 'store/product_form.html'
    success_url = reverse_lazy('product_list')

class ProductDeleteView(StoreManagerRequiredMixin, DeleteView):
    model = Product
    template_name = 'store/product_confirm_delete.html'
    success_url = reverse_lazy('product_list')