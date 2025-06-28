from django.urls import path
from . import views

urlpatterns = [
    # The homepage is now the product list view
    path('', views.ProductListView.as_view(), name='product_list'),
    # The detail view for a single product
    path('product/<int:pk>/', views.ProductDetailView.as_view(), name='product_detail'),

    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.view_cart, name='view_cart'),
    path('cart/remove/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),

    path('manage/product/new/', views.ProductCreateView.as_view(), name='product_create'),
    path('manage/product/<int:pk>/edit/', views.ProductUpdateView.as_view(), name='product_update'),
    path('manage/product/<int:pk>/delete/', views.ProductDeleteView.as_view(), name='product_delete'),
]