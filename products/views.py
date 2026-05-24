import stripe
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from products.forms import ProductForm, ReviewForm
from products.mixins import AuthorRequiredMixin
from products.models import CartItem, Category, Order, Product, Review
from products.services import (
    create_checkout_session,
    create_order_from_cart,
    fulfill_order,
    stripe_configured,
)


class HomeView(ListView):
    template_name = 'home.html'
    context_object_name = 'featured_products'

    def get_queryset(self):
        return Product.objects.select_related('category', 'author')[:6]


class ProductListView(ListView):
    model = Product
    template_name = 'products/products.html'
    context_object_name = 'products'
    paginate_by = 9

    def get_queryset(self):
        qs = Product.objects.select_related('category', 'author')
        category_id = self.request.GET.get('category_id')
        search = self.request.GET.get('search')
        sort = self.request.GET.get('sort', '-created_date')

        if category_id:
            qs = qs.filter(category_id=category_id)
        if search:
            qs = qs.filter(Q(title__icontains=search) | Q(description__icontains=search))

        sort_map = {
            'price_asc': 'price',
            'price_desc': '-price',
            'title': 'title',
            '-created_date': '-created_date',
        }
        return qs.order_by(sort_map.get(sort, '-created_date'))

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['categories'] = Category.objects.all()
        cat = self.request.GET.get('category_id')
        ctx['current_category'] = int(cat) if cat and cat.isdigit() else None
        ctx['search'] = self.request.GET.get('search', '')
        ctx['sort'] = self.request.GET.get('sort', '-created_date')
        return ctx


class ProductDetailView(DetailView):
    model = Product
    template_name = 'products/detail.html'
    context_object_name = 'product'
    pk_url_kwarg = 'id'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['reviews'] = self.object.reviews.select_related('user')
        ctx['form'] = ReviewForm()
        return ctx

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.product = self.object
            if request.user.is_authenticated:
                review.user = request.user
            review.save()
            messages.success(request, 'Отзыв добавлен.')
            return redirect('product-detail', id=self.object.pk)
        ctx = self.get_context_data()
        ctx['form'] = form
        return render(request, self.template_name, ctx)


class ProductCreateView(LoginRequiredMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = 'products/product_form.html'
    success_url = reverse_lazy('product-list')

    def form_valid(self, form):
        form.instance.author = self.request.user
        messages.success(self.request, 'Товар успешно создан.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Создать товар'
        return ctx


class ProductUpdateView(LoginRequiredMixin, AuthorRequiredMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = 'products/product_form.html'
    pk_url_kwarg = 'id'
    success_url = reverse_lazy('product-list')

    def form_valid(self, form):
        messages.success(self.request, 'Товар обновлён.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Редактировать товар'
        return ctx


class ProductDeleteView(LoginRequiredMixin, AuthorRequiredMixin, DeleteView):
    model = Product
    pk_url_kwarg = 'id'
    success_url = reverse_lazy('product-list')
    template_name = 'products/product_confirm_delete.html'

    def form_valid(self, form):
        messages.success(self.request, 'Товар удалён.')
        return super().form_valid(form)


class CategoryListView(ListView):
    model = Category
    template_name = 'categories/index.html'
    context_object_name = 'categories'


@login_required
def cart_view(request):
    items = CartItem.objects.filter(user=request.user).select_related('product')
    total = sum(item.subtotal for item in items)
    return render(request, 'products/cart.html', {'items': items, 'total': total})


@login_required
def cart_add(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    item, created = CartItem.objects.get_or_create(user=request.user, product=product)
    if not created:
        item.quantity += 1
        item.save()
    messages.success(request, f'«{product.title}» добавлен в корзину.')
    return redirect(request.META.get('HTTP_REFERER', 'product-list'))


@login_required
def cart_remove(request, item_id):
    CartItem.objects.filter(pk=item_id, user=request.user).delete()
    messages.info(request, 'Товар удалён из корзины.')
    return redirect('cart')


@login_required
def checkout_view(request):
    cart_items = list(
        CartItem.objects.filter(user=request.user).select_related('product')
    )
    if not cart_items:
        messages.warning(request, 'Корзина пуста.')
        return redirect('cart')

    if not stripe_configured():
        messages.error(
            request,
            'Stripe не настроен. Добавьте STRIPE_SECRET_KEY в .env (см. README).',
        )
        return redirect('cart')

    order = create_order_from_cart(request.user, cart_items)
    try:
        session = create_checkout_session(order, cart_items, request)
    except stripe.error.StripeError as exc:
        order.status = Order.STATUS_FAILED
        order.save(update_fields=['status'])
        messages.error(request, f'Ошибка Stripe: {exc.user_message if hasattr(exc, "user_message") else exc}')
        return redirect('cart')

    return redirect(session.url, code=303)


@login_required
def checkout_success_view(request):
    session_id = request.GET.get('session_id')
    order = None

    if session_id and stripe_configured():
        stripe.api_key = settings.STRIPE_SECRET_KEY
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            if session.payment_status == 'paid':
                order = Order.objects.filter(
                    stripe_session_id=session_id, user=request.user
                ).first()
                if order:
                    fulfill_order(order)
        except stripe.error.StripeError:
            messages.warning(request, 'Не удалось проверить статус оплаты.')

    if not order:
        order = (
            Order.objects.filter(user=request.user, status=Order.STATUS_PAID)
            .prefetch_related('items')
            .first()
        )

    if not order or not order.is_paid:
        messages.warning(request, 'Оплата ещё обрабатывается. Проверьте профиль позже.')
        return redirect('profile')

    return render(request, 'products/checkout_success.html', {'order': order})


@login_required
def checkout_cancel_view(request):
    session_id = request.GET.get('session_id')
    if session_id:
        Order.objects.filter(
            stripe_session_id=session_id,
            user=request.user,
            status=Order.STATUS_PENDING,
        ).update(status=Order.STATUS_CANCELLED)
    messages.info(request, 'Оплата отменена. Товары остались в корзине.')
    return redirect('cart')


@login_required
def profile_view(request):
    products = Product.objects.filter(author=request.user).select_related('category')
    orders = Order.objects.filter(user=request.user).prefetch_related('items')[:10]
    return render(request, 'users/profile.html', {
        'products': products,
        'orders': orders,
    })
