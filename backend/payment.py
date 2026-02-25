"""Stripe Payment Integration"""
from flask import Blueprint, request, jsonify, g, url_for
from datetime import datetime, timedelta
import os
import stripe
from .models import db, Product, Subscription, Payment, User
from .auth import require_auth, require_admin

payment_bp = Blueprint('payment', __name__, url_prefix='/api/payment')

# Stripe initialization
stripe_secret = os.getenv('STRIPE_SECRET_KEY')
if stripe_secret:
    stripe.api_key = stripe_secret
    STRIPE_ENABLED = True
else:
    STRIPE_ENABLED = False

PLATFORM_URL = os.getenv('PLATFORM_URL', 'http://localhost:8000')


@payment_bp.route('/plans', methods=['GET'])
def get_plans():
    """Get all product plans"""
    products = Product.query.filter_by(is_active=True).all()
    return jsonify([p.to_dict() for p in products]), 200


@payment_bp.route('/checkout', methods=['POST'])
@require_auth
def create_checkout_session():
    """Create Stripe checkout session"""
    if not STRIPE_ENABLED:
        return jsonify({'error': 'Payment not available in dev mode'}), 400

    data = request.get_json()
    product_id = data.get('product_id')
    plan_type = data.get('plan_type', 'monthly')  # 'monthly' or 'annual'

    product = Product.query.get(product_id)
    if not product:
        return jsonify({'error': 'Product not found'}), 404

    # Check if already subscribed
    existing = Subscription.query.filter_by(
        user_id=g.user_id,
        product_id=product_id,
        status='active'
    ).first()

    if existing:
        return jsonify({'error': 'Already subscribed to this product'}), 400

    try:
        price_id = product.stripe_price_id_monthly if plan_type == 'monthly' else product.stripe_price_id_annual

        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            mode='subscription',
            customer_email=g.user.email,
            success_url=f'{PLATFORM_URL}/api/payment/success?session_id={{CHECKOUT_SESSION_ID}}',
            cancel_url=f'{PLATFORM_URL}/web/platform/billing.html',
            metadata={
                'user_id': g.user_id,
                'product_id': product_id,
                'plan_type': plan_type
            }
        )

        return jsonify({'checkout_url': session.url}), 200

    except stripe.error.StripeError as e:
        return jsonify({'error': str(e)}), 400


@payment_bp.route('/success', methods=['GET'])
def checkout_success():
    """Handle Stripe checkout success"""
    if not STRIPE_ENABLED:
        return {'error': 'Payment not available'}, 400

    session_id = request.args.get('session_id')
    if not session_id:
        return {'error': 'Missing session_id'}, 400

    try:
        session = stripe.checkout.Session.retrieve(session_id)
        metadata = session.get('metadata', {})

        user_id = int(metadata.get('user_id'))
        product_id = int(metadata.get('product_id'))
        plan_type = metadata.get('plan_type', 'monthly')

        # Create subscription record
        subscription = Subscription(
            user_id=user_id,
            product_id=product_id,
            stripe_subscription_id=session.subscription,
            plan_type=plan_type,
            status='active',
            current_period_end=datetime.utcnow() + timedelta(days=30)
        )
        db.session.add(subscription)

        # Create payment record
        payment = Payment(
            user_id=user_id,
            product_id=product_id,
            stripe_payment_id=session.payment_intent,
            amount=session.amount_total / 100,
            status='completed'
        )
        db.session.add(payment)
        db.session.commit()

        return {'message': 'Payment successful'}, 200

    except stripe.error.StripeError as e:
        return {'error': str(e)}, 400


@payment_bp.route('/webhook', methods=['POST'])
def stripe_webhook():
    """Handle Stripe webhooks"""
    if not STRIPE_ENABLED:
        return {'error': 'Webhooks not enabled'}, 400

    payload = request.get_data()
    sig_header = request.headers.get('Stripe-Signature')
    webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET')

    if not webhook_secret:
        return {'error': 'Webhook secret not configured'}, 400

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)

        if event['type'] == 'customer.subscription.deleted':
            sub_id = event['data']['object']['id']
            subscription = Subscription.query.filter_by(stripe_subscription_id=sub_id).first()
            if subscription:
                subscription.status = 'canceled'
                db.session.commit()

        return {'message': 'Webhook received'}, 200

    except ValueError:
        return {'error': 'Invalid payload'}, 400
    except stripe.error.SignatureVerificationError:
        return {'error': 'Invalid signature'}, 400


@payment_bp.route('/subscriptions', methods=['GET'])
@require_auth
def get_subscriptions():
    """Get user subscriptions"""
    subscriptions = Subscription.query.filter_by(user_id=g.user_id).all()
    return jsonify([s.to_dict() for s in subscriptions]), 200


@payment_bp.route('/subscriptions/<int:subscription_id>', methods=['DELETE'])
@require_auth
def cancel_subscription(subscription_id):
    """Cancel a subscription"""
    subscription = Subscription.query.get(subscription_id)

    if not subscription:
        return jsonify({'error': 'Subscription not found'}), 404

    if subscription.user_id != g.user_id:
        return jsonify({'error': 'Not authorized'}), 403

    if STRIPE_ENABLED and subscription.stripe_subscription_id:
        try:
            stripe.Subscription.delete(subscription.stripe_subscription_id)
        except stripe.error.StripeError:
            pass

    subscription.status = 'canceled'
    db.session.commit()

    return jsonify({'message': 'Subscription canceled'}), 200
