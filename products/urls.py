from django.urls import path

from products import views
from products.stripe_views import stripe_webhook

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('products/', views.ProductListView.as_view(), name='product-list'),
    path('products/<int:id>/', views.ProductDetailView.as_view(), name='product-detail'),
    path('products/create/', views.ProductCreateView.as_view(), name='product-create'),
    path('products/<int:id>/edit/', views.ProductUpdateView.as_view(), name='product-edit'),
    path('products/<int:id>/delete/', views.ProductDeleteView.as_view(), name='product-delete'),
    path('categories/', views.CategoryListView.as_view(), name='category-list'),
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/<int:product_id>/', views.cart_add, name='cart-add'),
    path('cart/remove/<int:item_id>/', views.cart_remove, name='cart-remove'),
    path('checkout/', views.checkout_view, name='checkout'),
    path('checkout/success/', views.checkout_success_view, name='checkout-success'),
    path('checkout/cancel/', views.checkout_cancel_view, name='checkout-cancel'),
    path('stripe/webhook/', stripe_webhook, name='stripe-webhook'),
    path('profile/', views.profile_view, name='profile'),
]
