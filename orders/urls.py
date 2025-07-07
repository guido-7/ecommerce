from django.urls import path
from . import views

urlpatterns = [
    path('checkout/', views.checkout_address, name='checkout'),  # Step 1: Indirizzo
    path('checkout/process/', views.checkout_process, name='checkout_process'),  # Step 2: Processamento

    path('order/success/<int:order_id>/', views.order_success, name='order_success'),
    path('history/', views.OrderHistoryView.as_view(), name='order_history'),
]