from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.contrib.auth.models import User
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from products.models import CartItem, Category, Order, Product, Review
from products.services import fulfill_order


class ProductModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='tester', password='pass12345')
        self.category = Category.objects.create(title='Тест')

    def test_create_product(self):
        product = Product.objects.create(
            title='Тестовый товар',
            description='Описание',
            price=Decimal('1000.00'),
            category=self.category,
            author=self.user,
        )
        self.assertEqual(str(product), 'Тестовый товар')
        self.assertEqual(product.category, self.category)

    def test_create_review(self):
        product = Product.objects.create(
            title='Товар',
            description='Описание',
            price=Decimal('500'),
            author=self.user,
        )
        review = Review.objects.create(product=product, review='Отлично!', user=self.user)
        self.assertEqual(product.reviews.count(), 1)
        self.assertIn('Отлично', str(review))


@override_settings(STRIPE_SECRET_KEY='sk_test_fake')
class ProductViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='buyer', password='pass12345')
        self.author = User.objects.create_user(username='seller', password='pass12345')
        self.category = Category.objects.create(title='Категория')
        self.product = Product.objects.create(
            title='Телефон',
            description='Смартфон',
            price=Decimal('100000'),
            category=self.category,
            author=self.author,
        )

    def test_home_page(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)

    def test_product_list(self):
        response = self.client.get(reverse('product-list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Телефон')

    def test_product_search(self):
        response = self.client.get(reverse('product-list'), {'search': 'Телефон'})
        self.assertContains(response, 'Телефон')

    def test_product_detail(self):
        response = self.client.get(reverse('product-detail', kwargs={'id': self.product.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Телефон')

    def test_product_detail_404(self):
        response = self.client.get(reverse('product-detail', kwargs={'id': 9999}))
        self.assertEqual(response.status_code, 404)

    def test_create_requires_login(self):
        response = self.client.get(reverse('product-create'))
        self.assertEqual(response.status_code, 302)

    def test_create_product(self):
        self.client.login(username='seller', password='pass12345')
        response = self.client.post(reverse('product-create'), {
            'title': 'Новый',
            'description': 'Описание нового',
            'price': '5000',
            'category': self.category.pk,
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Product.objects.filter(title='Новый').exists())

    def test_add_review(self):
        self.client.login(username='buyer', password='pass12345')
        response = self.client.post(reverse('product-detail', kwargs={'id': self.product.pk}), {
            'review': 'Супер товар!',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Review.objects.filter(review='Супер товар!').exists())

    def test_cart_add(self):
        self.client.login(username='buyer', password='pass12345')
        response = self.client.get(reverse('cart-add', kwargs={'product_id': self.product.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(CartItem.objects.filter(user=self.user).count(), 1)

    @patch('products.views.create_checkout_session')
    def test_checkout_redirects_to_stripe(self, mock_create_session):
        mock_session = MagicMock()
        mock_session.url = 'https://checkout.stripe.com/test'
        mock_create_session.return_value = mock_session

        self.client.login(username='buyer', password='pass12345')
        CartItem.objects.create(user=self.user, product=self.product, quantity=1)

        response = self.client.get(reverse('checkout'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, 'https://checkout.stripe.com/test')
        self.assertEqual(Order.objects.filter(user=self.user, status=Order.STATUS_PENDING).count(), 1)
        self.assertEqual(CartItem.objects.filter(user=self.user).count(), 1)

    def test_fulfill_order_clears_cart(self):
        self.client.login(username='buyer', password='pass12345')
        CartItem.objects.create(user=self.user, product=self.product, quantity=1)
        order = Order.objects.create(
            user=self.user, total=Decimal('100000'), status=Order.STATUS_PENDING
        )
        fulfill_order(order)
        self.assertEqual(order.status, Order.STATUS_PAID)
        self.assertEqual(CartItem.objects.filter(user=self.user).count(), 0)


@override_settings(STRIPE_SECRET_KEY='')
class CheckoutWithoutStripeTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='buyer', password='pass12345')
        self.author = User.objects.create_user(username='seller', password='pass12345')
        self.product = Product.objects.create(
            title='Товар',
            description='Desc',
            price=Decimal('100'),
            author=self.author,
        )

    def test_checkout_without_stripe_keys(self):
        self.client.login(username='buyer', password='pass12345')
        CartItem.objects.create(user=self.user, product=self.product)
        response = self.client.get(reverse('checkout'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(CartItem.objects.filter(user=self.user).count(), 1)
