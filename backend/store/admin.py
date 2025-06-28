from django.contrib import admin
from .models import Category, Product, ProductImage

# Inline admin to manage ProductImage within the Product admin page
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1  # number of empty slots for new images

# Customized Product admin with inline images
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'stock')
    list_filter = ('category',)
    search_fields = ('name', 'description')
    inlines = [ProductImageInline]

# Category admin
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}

# Optional: separate admin for standalone Image management
@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('product', 'image')
    list_filter = ('product',)
