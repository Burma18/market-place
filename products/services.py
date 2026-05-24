from decimal import Decimal

import stripe
from django.conf import settings
from django.db import transaction

from products.models import CartItem, Order, OrderItem


def stripe_configured():
    return bool(settings.STRIPE_SECRET_KEY)


def _amount_in_tyiyin(price: Decimal) -> int:
    """Stripe для KGS принимает сумму в тыйынах (1 сом = 100 тыйын)."""
    return int(price * 100)


def create_order_from_cart(user, cart_items):
    total = sum(item.subtotal for item in cart_items)
    order = Order.objects.create(user=user, total=total, status=Order.STATUS_PENDING)
    for item in cart_items:
        OrderItem.objects.create(
            order=order,
            product=item.product,
            title=item.product.title,
            price=item.product.price,
            quantity=item.quantity,
        )
    return order


def create_checkout_session(order, cart_items, request):
    stripe.api_key = settings.STRIPE_SECRET_KEY

    line_items = [
        {
            'price_data': {
                'currency': 'kgs',
                'product_data': {'name': item.product.title[:120]},
                'unit_amount': _amount_in_tyiyin(item.product.price),
            },
            'quantity': item.quantity,
        }
        for item in cart_items
    ]

    session = stripe.checkout.Session.create(
        mode='payment',
        line_items=line_items,
        success_url=(
            request.build_absolute_uri('/checkout/success/')
            + '?session_id={CHECKOUT_SESSION_ID}'
        ),
        cancel_url=request.build_absolute_uri('/checkout/cancel/'),
        metadata={'order_id': str(order.pk)},
        client_reference_id=str(order.pk),
    )
    order.stripe_session_id = session.id
    order.save(update_fields=['stripe_session_id'])
    return session


@transaction.atomic
def fulfill_order(order):
    if order.is_paid:
        return order
    order.status = Order.STATUS_PAID
    order.save(update_fields=['status'])
    CartItem.objects.filter(user=order.user).delete()
    return order


def get_order_from_session(session):
    order_id = session.get('metadata', {}).get('order_id')
    if order_id:
        return Order.objects.filter(pk=order_id).first()
    session_id = session.get('id')
    if session_id:
        return Order.objects.filter(stripe_session_id=session_id).first()
    return None
