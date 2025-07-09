from decimal import Decimal

from django.db import models
from django.conf import settings
from store.models import Product

class Order(models.Model):
    class OrderStatus(models.TextChoices):
        # Chiave = 'valore', 'descrizione'
        PENDING = 'Pending', 'Pending'
        SHIPPED = 'Shipped', 'Shipped'
        DELIVERED = 'Delivered', 'Delivered'
        CANCELLED = 'Cancelled', 'Cancelled'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    street_address = models.CharField("Street address", max_length=255)
    city = models.CharField("City", max_length=100)
    postal_code = models.CharField("ZIP code", max_length=20)
    country = models.CharField("Country", max_length=100)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    promo_code_used = models.CharField(max_length=20, blank=True, null=True)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))

    status = models.CharField(
        max_length=10,
        choices=OrderStatus.choices,
        default=OrderStatus.PENDING
    )

    def __str__(self):
        return f"Order {self.id} by {self.user.username}"

    def get_subtotal(self):
        """ Calcola il subtotale prima dello sconto """
        return self.total_amount + self.discount_amount

    def get_savings(self):
        """Restituisce il totale risparmiato"""
        # Calcola risparmi dai prodotti scontati
        product_savings = Decimal('0.00')
        for item in self.items.all():
            if item.product.discounted_price:
                original_price = item.product.price
                discounted_price = item.product.discounted_price
                product_savings += (original_price - discounted_price) * item.quantity

        # Aggiungi lo sconto del promo code
        return product_savings + self.discount_amount

    class Meta:
        ordering = ['-created_at']


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    product_name = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity} of {self.product.name}"