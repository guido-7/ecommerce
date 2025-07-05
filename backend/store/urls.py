from django.urls import path
from . import views
from .views import update_order_status

urlpatterns = [
    # The homepage is now the product list view
    path('', views.ProductListView.as_view(), name='product_list'),
    # The detail view for a single product
    path('product/<int:pk>/', views.ProductDetailView.as_view(), name='product_detail'),

    path('cart/', views.view_cart, name='view_cart'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/update/<int:product_id>/', views.update_cart_quantity, name='update_cart_quantity'),

    # Promo Code
    path('cart/apply-promo/', views.apply_promo_code, name='apply_promo_code'),
    path('cart/remove-promo/', views.remove_promo_code, name='remove_promo_code'),

    # Management URLs
    path('manage/', views.ManageView.as_view(), name='manage'),

    path('manage/product/new/', views.ProductCreateView.as_view(), name='product_create'),
    path('manage/product/<int:pk>/edit/', views.ProductUpdateView.as_view(), name='product_update'),
    path('manage/product/<int:pk>/delete/', views.ProductDeleteView.as_view(), name='product_delete'),

    # Category CRUD
    path('manage/category/new/', views.CategoryCreateView.as_view(), name='category_create'),
    path('manage/category/<int:pk>/edit/', views.CategoryUpdateView.as_view(), name='category_update'),
    path('manage/category/<int:pk>/delete/', views.CategoryDeleteView.as_view(), name='category_delete'),

    # Brand CRUD
    path('manage/brand/new/', views.BrandCreateView.as_view(), name='brand_create'),
    path('manage/brand/<int:pk>/edit/', views.BrandUpdateView.as_view(), name='brand_update'),
    path('manage/brand/<int:pk>/delete/', views.BrandDeleteView.as_view(), name='brand_delete'),

    path('order/<int:pk>/update-status/', update_order_status, name='update_order_status'),
]
