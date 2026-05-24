# ShopKG — Django E-commerce Portfolio

Интернет-магазин на **Django 4.1** с каталогом товаров, корзиной, отзывами, авторизацией и личным кабинетом. Проект создан для демонстрации навыков backend-разработки в портфолио.

## Что демонстрирует проект

- **Django ORM** — модели с связями, миграции, QuerySet-фильтрация и сортировка
- **Class-Based Views** — ListView, DetailView, CreateView, UpdateView, DeleteView
- **Аутентификация** — регистрация, вход, logout, защита views через `LoginRequiredMixin`
- **Forms & Media** — ModelForm, загрузка изображений товаров
- **Пагинация** — встроенный Paginator с сохранением фильтров
- **Корзина и оплата** — Stripe Checkout (test mode), webhook, OrderItem
- **Тесты** — unit-тесты моделей и views
- **Деплой** — Gunicorn, WhiteNoise, PostgreSQL (Render)
- **Docker** — Dockerfile + docker-compose (web + PostgreSQL)

## Скриншоты

> Добавьте скриншоты в `docs/screenshots/` после запуска проекта:
> `home.png`, `catalog.png`, `product-detail.png`

## Быстрый старт

```bash
git clone <url-репозитория>
cd Django_4m
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

Откройте [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

### Демо-аккаунт

| Логин | Пароль |
|-------|--------|
| `demo` | `demo12345` |
| `admin` | `admin12345` (суперпользователь) |

## Основные URL

| URL | Описание |
|-----|----------|
| `/` | Главная с популярными товарами |
| `/products/` | Каталог (поиск, фильтр, сортировка) |
| `/products/<id>/` | Карточка товара + отзывы |
| `/products/create/` | Создать товар (авторизован) |
| `/cart/` | Корзина |
| `/checkout/` | Оплата через Stripe Checkout |
| `/checkout/success/` | Успешная оплата |
| `/stripe/webhook/` | Webhook Stripe |
| `/profile/` | Профиль и история заказов |
| `/categories/` | Список категорий |
| `/users/login/` | Вход |
| `/users/register/` | Регистрация |
| `/admin/` | Админ-панель |

## Stripe (тестовый режим)

1. Зарегистрируйтесь на [dashboard.stripe.com](https://dashboard.stripe.com/register) и включите **Test mode**.
2. Скопируйте ключи в `.env` (см. `.env.example`):
   - `STRIPE_PUBLIC_KEY` — `pk_test_...`
   - `STRIPE_SECRET_KEY` — `sk_test_...`
3. Для webhook локально установите [Stripe CLI](https://stripe.com/docs/stripe-cli):

```bash
stripe listen --forward-to localhost:8000/stripe/webhook/
```

Скопируйте `whsec_...` в `STRIPE_WEBHOOK_SECRET`.

4. Добавьте товары в корзину → **Оплатить через Stripe**.
5. Тестовая карта: `4242 4242 4242 4242`, срок и CVC — любые будущие значения.

Валюта заказов: **KGS** (кыргызский сом).

## Docker

Требуется [Docker Desktop](https://www.docker.com/products/docker-desktop/) (или Docker Engine + Compose).

**Ошибка `docker-credential-desktop: executable file not found`:** в `~/.docker/config.json` удалите строку `"credsStore": "desktop"` или переустановите/запустите Docker Desktop.

```bash
cp .env.docker.example .env
# Добавьте STRIPE_SECRET_KEY в .env при необходимости

docker compose up --build
```

Приложение: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

При первом запуске автоматически выполняются: миграции, `collectstatic`, `seed_demo` (если `SEED_DEMO=true`).

### Полезные команды

```bash
# Остановить
docker compose down

# Логи
docker compose logs -f web

# Shell в контейнере
docker compose exec web python manage.py shell

# Создать суперпользователя
docker compose exec web python manage.py createsuperuser

# Пересобрать после изменений кода
docker compose up --build
```

Сервисы:
- **web** — Django + Gunicorn (порт 8000)
- **db** — PostgreSQL 15

Данные сохраняются в Docker volumes: `postgres_data`, `media_data`.

## Тесты

```bash
python manage.py test
```

## Деплой на Render

1. Создайте PostgreSQL и Web Service на [render.com](https://render.com)
2. Подключите репозиторий, укажите `buildCommand`: `./build.sh`
3. Задайте переменные окружения:
   - `SECRET_KEY` — случайная строка
   - `DEBUG=False`
   - `ALLOWED_HOSTS=your-app.onrender.com`
   - `DATABASE_URL` — из PostgreSQL
   - `CSRF_TRUSTED_ORIGINS=https://your-app.onrender.com`

Или используйте `render.yaml` для Blueprint-деплоя.

## Стек

- Python 3.9+
- Django 4.1.5
- SQLite (локально) / PostgreSQL (прод)
- Bootstrap 5
- Pillow, WhiteNoise, Gunicorn

## Структура

```
Django_4m/       # settings, urls, wsgi
products/        # модели, views, forms, cart
users/           # auth views
templates/       # HTML-шаблоны
static/          # CSS, placeholder
Dockerfile       # образ приложения
docker-compose.yml
entrypoint.sh    # migrate + collectstatic при старте
```

## Возможное развитие

- REST API (DRF)
- Email-уведомления о заказах
- Cloudinary для медиа на проде
- i18n (EN/KG)
