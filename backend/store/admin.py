from django.contrib import admin
from .models import Category, Product, ProductImage, Brand


# Inline admin to manage ProductImage within the Product admin page
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1  # number of empty slots for new images

# Customized Product admin with inline images
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'brand', 'category', 'price', 'discounted_price', 'stock')
    list_filter = ( 'brand', 'category')
    search_fields = ('name', 'brand__name', 'category__name', 'description')
    autocomplete_fields = ('brand', 'category')
    inlines = [ProductImageInline]

# Category admin
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']

@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']

# Optional: separate admin for standalone Image management
@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('product', 'image')
    list_filter = ('product',)
