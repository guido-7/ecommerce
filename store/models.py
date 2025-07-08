from cloudinary.models import CloudinaryField
from cloudinary.uploader import destroy
from django.db import models
from django.utils import timezone

class Category(models.Model):
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True, help_text="Unique URL-friendly name for the category.")

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name

class Brand(models.Model):
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True)

    def __str__(self):
        return self.name

class Product(models.Model):
    category = models.ForeignKey(Category, related_name='products', on_delete=models.CASCADE)
    brand = models.ForeignKey(Brand, related_name='products', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discounted_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Discounted Price",
        help_text="Price after discount, if applicable."
    )
    stock = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    @property
    def is_available(self):
        return self.stock > 0

    def get_actual_price(self):
        return self.discounted_price if self.discounted_price is not None else self.price


class ProductImage(models.Model):
    product = models.ForeignKey(Product, related_name='images', on_delete=models.CASCADE)
    image = CloudinaryField('image', folder='media/products/')

    def __str__(self):
        return f"Image for {self.product.name}"


class PromoCode(models.Model):
    code = models.CharField(max_length=20, unique=True)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()

    def __str__(self):
        return self.code

    def is_valid(self):
        if not self.valid_from or not self.valid_to:
            return False

        now = timezone.now()
        return self.valid_from <= now <= self.valid_to