import json
import logging

import stripe
from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from products.services import fulfill_order, get_order_from_session, stripe_configured

logger = logging.getLogger(__name__)


@csrf_exempt
@require_POST
def stripe_webhook(request):
    if not stripe_configured():
        return HttpResponseBadRequest('Stripe not configured')

    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE', '')

    try:
        if settings.STRIPE_WEBHOOK_SECRET:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
        else:
            event = json.loads(payload)
    except (ValueError, stripe.error.SignatureVerificationError) as exc:
        logger.warning('Stripe webhook error: %s', exc)
        return HttpResponseBadRequest('Invalid payload')

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        order = get_order_from_session(session)
        if order:
            fulfill_order(order)

    return HttpResponse(status=200)
