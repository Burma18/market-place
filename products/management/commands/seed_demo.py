from decimal import Decimal

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from products.models import Category, Product, Review


class Command(BaseCommand):
    help = 'Заполняет базу демо-данными для портфолио'

    def handle(self, *args, **options):
        if Product.objects.exists() and not options.get('force'):
            self.stdout.write(self.style.WARNING('Данные уже есть. Используйте --force для перезаписи.'))
            return

        Product.objects.all().delete()
        Category.objects.all().delete()
        Review.objects.all().delete()

        demo_user, created = User.objects.get_or_create(
            username='demo',
            defaults={'email': 'demo@shopkg.local'},
        )
        if created:
            demo_user.set_password('demo12345')
            demo_user.save()
            self.stdout.write(self.style.SUCCESS('Создан пользователь demo / demo12345'))

        admin, _ = User.objects.get_or_create(
            username='admin',
            defaults={'email': 'admin@shopkg.local', 'is_staff': True, 'is_superuser': True},
        )
        if _:
            admin.set_password('admin12345')
            admin.save()

        categories_data = [
            'Электроника',
            'Одежда',
            'Книги',
            'Спорт',
            'Дом и сад',
            'Красота',
            'Игрушки',
            'Продукты',
        ]
        categories = [Category.objects.create(title=t) for t in categories_data]

        products_data = [
            ('iPhone 15', 'Смартфон Apple с отличной камерой и производительностью.', 450000, 0),
            ('Samsung Galaxy S24', 'Флагманский Android-смартфон с AI-функциями.', 420000, 0),
            ('MacBook Air M3', 'Лёгкий ноутбук для работы и учёбы.', 650000, 0),
            ('Sony WH-1000XM5', 'Беспроводные наушники с шумоподавлением.', 180000, 0),
            ('Джинсы Levi\'s 501', 'Классические прямые джинсы из денима.', 35000, 1),
            ('Куртка North Face', 'Зимняя куртка с мембраной Gore-Tex.', 120000, 1),
            ('Футболка Nike Dri-FIT', 'Спортивная футболка с влагоотводом.', 12000, 1),
            ('Кроссовки Adidas Ultraboost', 'Беговые кроссовки с Boost-подошвой.', 85000, 4),
            ('Велосипед горный', 'MTB велосипед 21 скорость, алюминиевая рама.', 250000, 4),
            ('Гантели 2x10 кг', 'Набор гантелей для домашних тренировок.', 25000, 4),
            ('«Война и мир»', 'Классический роман Л.Н. Толстого.', 4500, 2),
            ('«Clean Code»', 'Книга Роберта Мартина о чистом коде.', 8000, 2),
            ('«Django for Professionals»', 'Практическое руководство по Django.', 12000, 2),
            ('Кофемашина DeLonghi', 'Автоматическая кофемашина для эспрессо.', 95000, 5),
            ('Набор кастрюль', '5 предметов, нержавеющая сталь.', 45000, 5),
            ('Пылесос Dyson V15', 'Беспроводной пылесос с лазерной подсветкой.', 280000, 5),
            ('Крем для лица', 'Увлажняющий крем с гиалуроновой кислотой.', 8500, 6),
            ('Набор кистей для макияжа', '12 профессиональных кистей.', 15000, 6),
            ('Конструктор LEGO City', 'Набор 500 деталей для детей 6+.', 22000, 7),
            ('Плюшевый мишка', 'Мягкая игрушка 50 см.', 6500, 7),
            ('Оливковое масло Extra Virgin', '1 литр, холодный отжим.', 3500, 7),
            ('Набор специй', '12 видов специй в подарочной коробке.', 5500, 7),
            ('Планшет iPad Air', '10.9" дисплей, чип M1.', 380000, 0),
            ('Умные часы Apple Watch', 'Series 9, GPS + Cellular.', 220000, 0),
            ('Рюкзак туристический', 'Объём 50л, водонепроницаемый.', 18000, 4),
        ]

        products = []
        for title, desc, price, cat_idx in products_data:
            p = Product.objects.create(
                title=title,
                description=desc,
                price=Decimal(price),
                category=categories[cat_idx],
                author=demo_user,
            )
            products.append(p)

        reviews_texts = [
            'Отличный товар, рекомендую!',
            'Качество на высоте, доставка быстрая.',
            'Хорошее соотношение цена/качество.',
            'Покупкой доволен, буду заказывать ещё.',
            'Немного дороговато, но того стоит.',
        ]
        for i, product in enumerate(products[:10]):
            Review.objects.create(
                product=product,
                review=reviews_texts[i % len(reviews_texts)],
                user=demo_user,
            )

        self.stdout.write(self.style.SUCCESS(
            f'Готово: {len(categories)} категорий, {len(products)} товаров, '
            f'{Review.objects.count()} отзывов'
        ))

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true', help='Перезаписать существующие данные')
