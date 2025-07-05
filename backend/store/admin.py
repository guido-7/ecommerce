from django.contrib import admin
from .models import Category, Product, ProductImage, Brand, PromoCode


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

@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('product', 'image')
    list_filter = ('product',)

@admin.register(PromoCode)
class PromoCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_percentage', 'valid_from', 'valid_to', 'is_valid')
    list_filter = ('valid_from', 'valid_to', 'discount_percentage')
    search_fields = ('code',)
    readonly_fields = ('is_valid',)

    def is_valid(self, obj):
        return obj.is_valid()

    is_valid.boolean = True
    is_valid.short_description = 'Valido'

    # Ordina per data di validità
    ordering = ('-valid_from',)