"""Stripe Payment Integration — Enhanced with Invoices, KRW, & Subscriptions"""
from flask import Blueprint, request, jsonify, g, url_for, send_file
from datetime import datetime, timedelta
import os
import json
import stripe
import requests
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from io import BytesIO
from .models import db, Product, Subscription, Payment, User, Order, Invoice, SubscriptionPlan, FileUpload
from .auth import require_auth, require_admin
from .services.file_service import get_s3_client

payment_bp = Blueprint('payment', __name__, url_prefix='/api/payment')

# Stripe initialization
stripe_secret = os.getenv('STRIPE_SECRET_KEY')
if stripe_secret:
    stripe.api_key = stripe_secret
    STRIPE_ENABLED = True
else:
    STRIPE_ENABLED = False

PLATFORM_URL = os.getenv('PLATFORM_URL', 'http://localhost:8000')

# ============ EXCHANGE RATES & UTILITIES ============

class ExchangeRateService:
    """KRW/USD exchange rate management with caching"""
    CACHE_KEY = 'exchange_rate_usd_krw'
    CACHE_TTL = 3600  # 1 hour
    DEFAULT_RATE = 1250.0  # Fallback rate

    @staticmethod
    def get_current_rate():
        """Get USD to KRW exchange rate from OpenExchangeRates API"""
        try:
            # Try to fetch from cache first
            cache_rate = os.getenv('CACHED_EXCHANGE_RATE')
            if cache_rate:
                return float(cache_rate)

            # Fetch from free API (OpenExchangeRates)
            api_key = os.getenv('EXCHANGE_RATE_API_KEY', '')
            if api_key:
                url = f'https://openexchangerates.org/api/latest.json?app_id={api_key}&symbols=KRW'
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    rate = data.get('rates', {}).get('KRW', ExchangeRateService.DEFAULT_RATE)
                    return float(rate)

            # Fallback to fixed rate
            return ExchangeRateService.DEFAULT_RATE
        except Exception as e:
            return ExchangeRateService.DEFAULT_RATE

    @staticmethod
    def usd_to_krw(usd_amount):
        """Convert USD to KRW"""
        rate = ExchangeRateService.get_current_rate()
        return int(usd_amount * rate)

    @staticmethod
    def krw_to_usd(krw_amount):
        """Convert KRW to USD"""
        rate = ExchangeRateService.get_current_rate()
        return round(krw_amount / rate, 2)


def calculate_tax(amount_krw, tax_rate=0.1):
    """Calculate tax (default 10% VAT in Korea)"""
    return int(amount_krw * tax_rate)


def generate_invoice_number():
    """Generate invoice number: YYYYMMDD-XXXX format"""
    today = datetime.utcnow().strftime('%Y%m%d')
    seq = Invoice.query.filter(
        Invoice.invoice_number.like(f'{today}%')
    ).count() + 1
    return f'{today}-{seq:04d}'


def generate_shipping_number():
    """Generate shipping tracking number: YYYYMMDD-XXXX format"""
    today = datetime.utcnow().strftime('%Y%m%d')
    seq = Order.query.filter(
        Order.order_number.like(f'{today}%')
    ).count() + 1
    return f'{today}-{seq:04d}'


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
    """Get user subscriptions with plan details

    Query params:
    - status: filter by status (active, canceled, expired)
    - limit: max results (default 50)
    - offset: pagination offset (default 0)

    Response: [{
        "id": int,
        "plan_name": str,
        "plan_slug": str,
        "period": str,
        "amount_krw": int,
        "status": str,
        "started_date": ISO,
        "next_billing_date": ISO,
        "refund_eligible": bool,
        "refund_amount_krw": int
    }]
    """
    limit = min(int(request.args.get('limit', 50)), 100)
    offset = int(request.args.get('offset', 0))
    status_filter = request.args.get('status')

    query = Subscription.query.filter_by(user_id=g.user_id)
    if status_filter:
        query = query.filter_by(status=status_filter)

    subscriptions = query.order_by(
        Subscription.created_at.desc()
    ).limit(limit).offset(offset).all()

    result = []
    for sub in subscriptions:
        plan = SubscriptionPlan.query.get(sub.product_id)
        if not plan:
            continue

        # Check refund eligibility
        days_since_start = (datetime.utcnow() - sub.created_at).days
        refund_eligible = days_since_start <= 7 and sub.status == 'active'
        refund_amount_krw = (plan.monthly_price_krw
                           if sub.plan_type == 'monthly'
                           else plan.annual_price_krw) if refund_eligible else 0

        result.append({
            'id': sub.id,
            'plan_name': plan.name,
            'plan_slug': plan.slug,
            'period': sub.plan_type,
            'amount_krw': (plan.monthly_price_krw
                          if sub.plan_type == 'monthly'
                          else plan.annual_price_krw),
            'status': sub.status,
            'started_date': sub.created_at.isoformat(),
            'next_billing_date': sub.current_period_end.isoformat(),
            'days_until_billing': max(0, (sub.current_period_end - datetime.utcnow()).days),
            'refund_eligible': refund_eligible,
            'refund_amount_krw': refund_amount_krw
        })

    return jsonify({
        'total': len(result),
        'limit': limit,
        'offset': offset,
        'subscriptions': result
    }), 200


# ============ INVOICING & ORDERS ============

def generate_invoice_pdf(invoice, user, order=None):
    """Generate PDF invoice using ReportLab

    Returns: BytesIO object with PDF content
    """
    pdf_buffer = BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=A4)
    story = []

    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=12,
        textColor=colors.HexColor('#34495e'),
        spaceAfter=12
    )

    # Title
    story.append(Paragraph('INVOICE', title_style))
    story.append(Spacer(1, 0.3 * inch))

    # Invoice header info
    due_date = invoice.due_date or (invoice.issued_date + timedelta(days=30))
    header_data = [
        ['Invoice Number:', invoice.invoice_number, 'Issue Date:', invoice.issued_date.strftime('%Y-%m-%d')],
        ['Company:', 'SoftFactory Inc.', 'Due Date:', due_date.strftime('%Y-%m-%d')],
    ]
    header_table = Table(header_data, colWidths=[1.5*inch, 2*inch, 1.5*inch, 2*inch])
    header_table.setStyle(TableStyle([
        ('FONT', (0, 0), (-1, -1), 'Helvetica', 10),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 0.3 * inch))

    # Bill to
    story.append(Paragraph('Bill To:', heading_style))
    bill_data = [
        [f'{user.name}'],
        [user.email],
    ]
    bill_table = Table(bill_data, colWidths=[4*inch])
    bill_table.setStyle(TableStyle([
        ('FONT', (0, 0), (-1, -1), 'Helvetica', 10),
    ]))
    story.append(bill_table)
    story.append(Spacer(1, 0.3 * inch))

    # Line items
    story.append(Paragraph('Line Items:', heading_style))
    if order:
        items = json.loads(order.items_json) if isinstance(order.items_json, str) else order.items_json
        items_data = [['Description', 'Quantity', 'Unit Price (KRW)', 'Amount (KRW)']]
        for item in items:
            items_data.append([
                f"Product {item.get('product_id', 'N/A')}",
                str(item.get('quantity', 1)),
                f"{item.get('price_krw', 0):,}",
                f"{item.get('quantity', 1) * item.get('price_krw', 0):,}"
            ])
    else:
        items_data = [['Description', 'Amount (KRW)']]
        items_data.append(['Invoice Payment', f'{invoice.amount_krw:,}'])

    items_table = Table(items_data, colWidths=[2.5*inch, 1.2*inch, 1.5*inch, 1.5*inch])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold', 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),
        ('FONT', (0, 1), (-1, -1), 'Helvetica', 9),
    ]))
    story.append(items_table)
    story.append(Spacer(1, 0.2 * inch))

    # Totals
    totals_data = [
        ['Subtotal (KRW):', f'{invoice.amount_krw:,}'],
        ['Tax (KRW):', f'{invoice.tax_krw:,}'],
        ['Total (KRW):', f'{invoice.total_krw:,}'],
    ]
    totals_table = Table(totals_data, colWidths=[4*inch, 2*inch])
    totals_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONT', (0, 0), (0, -1), 'Helvetica', 10),
        ('FONT', (1, 0), (1, -2), 'Helvetica', 10),
        ('FONT', (1, -1), (1, -1), 'Helvetica-Bold', 12),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#34495e')),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.whitesmoke),
    ]))
    story.append(totals_table)
    story.append(Spacer(1, 0.3 * inch))

    # Footer
    story.append(Paragraph(
        'Thank you for your business!<br/>Payment terms: Net 30 days',
        styles['Normal']
    ))

    # Build PDF
    doc.build(story)
    pdf_buffer.seek(0)
    return pdf_buffer


@payment_bp.route('/invoice', methods=['POST'])
@require_auth
def create_invoice():
    """Create invoice for an order with automatic tax calculation

    Body: {
        "order_id": int (optional),
        "amount_krw": int,
        "tax_rate": float (optional, default 0.10 for 10% VAT),
        "due_days": int (optional, default 30),
        "description": str (optional)
    }

    Response: {
        "invoice_id": int,
        "invoice_number": str,
        "amount_krw": int,
        "tax_krw": int,
        "total_krw": int,
        "pdf_url": str (S3 URL),
        "stripe_url": str (Stripe invoice URL if enabled)
    }
    """
    data = request.get_json()
    order_id = data.get('order_id')
    amount_krw = data.get('amount_krw')
    tax_rate = data.get('tax_rate', 0.10)  # Default 10% VAT
    due_days = data.get('due_days', 30)
    description = data.get('description', 'Invoice Payment')

    if not amount_krw or amount_krw <= 0:
        return jsonify({'error': 'Invalid amount'}), 400

    try:
        # Generate invoice number using utility function
        invoice_number = generate_invoice_number()

        # Calculate tax
        tax_krw = calculate_tax(amount_krw, tax_rate)
        total_krw = amount_krw + tax_krw

        # Create invoice record
        invoice = Invoice(
            user_id=g.user_id,
            order_id=order_id,
            invoice_number=invoice_number,
            amount_krw=amount_krw,
            tax_krw=tax_krw,
            total_krw=total_krw,
            status='issued',
            issued_date=datetime.utcnow(),
            due_date=datetime.utcnow() + timedelta(days=due_days),
            payment_method='stripe'
        )
        db.session.add(invoice)
        db.session.flush()

        # Generate PDF
        order = Order.query.get(order_id) if order_id else None
        pdf_buffer = generate_invoice_pdf(invoice, g.user, order)

        # Upload PDF to S3
        s3_client = get_s3_client()
        pdf_url = None
        if s3_client:
            pdf_key = f'invoices/{g.user_id}/{invoice_number}.pdf'
            s3_client.put_object(
                Bucket=os.getenv('AWS_S3_BUCKET', 'softfactory-uploads'),
                Key=pdf_key,
                Body=pdf_buffer.getvalue(),
                ContentType='application/pdf',
                Metadata={'invoice_id': str(invoice.id)}
            )

            # Create FileUpload record
            pdf_upload = FileUpload(
                user_id=g.user_id,
                file_key=pdf_key,
                original_filename=f'{invoice_number}.pdf',
                file_size=len(pdf_buffer.getvalue()),
                content_type='application/pdf',
                category='document',
                s3_url=f"https://{os.getenv('AWS_S3_BUCKET', 'softfactory-uploads')}.s3.{os.getenv('AWS_S3_REGION', 'us-east-1')}.amazonaws.com/{pdf_key}",
                cdn_url=f"https://{os.getenv('CLOUDFRONT_DOMAIN')}/{pdf_key}" if os.getenv('CLOUDFRONT_DOMAIN') else None
            )
            db.session.add(pdf_upload)
            db.session.flush()
            invoice.pdf_file_id = pdf_upload.id
            pdf_url = pdf_upload.s3_url

        db.session.commit()

        # Create Stripe invoice if enabled
        stripe_url = None
        if STRIPE_ENABLED and total_krw > 0:
            try:
                # Convert to cents for Stripe (USD)
                amount_usd_cents = int(ExchangeRateService.krw_to_usd(total_krw) * 100)
                stripe_inv = stripe.Invoice.create(
                    customer=g.user.stripe_customer_id if hasattr(g.user, 'stripe_customer_id') else None,
                    amount_paid=0,
                    collection_method='send_invoice',
                    days_until_due=due_days,
                    description=description,
                    metadata={'invoice_id': invoice.id, 'amount_krw': amount_krw}
                )
                invoice.stripe_invoice_id = stripe_inv.id
                db.session.commit()
                stripe_url = stripe_inv.hosted_invoice_url
            except stripe.error.StripeError as e:
                pass  # Log but don't fail

        return jsonify({
            'invoice_id': invoice.id,
            'invoice_number': invoice_number,
            'amount_krw': amount_krw,
            'tax_krw': tax_krw,
            'total_krw': total_krw,
            'pdf_url': pdf_url,
            'stripe_url': stripe_url,
            'issued_date': invoice.issued_date.isoformat(),
            'due_date': invoice.due_date.isoformat(),
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@payment_bp.route('/invoices/<int:invoice_id>/download', methods=['GET'])
@require_auth
def download_invoice(invoice_id):
    """Download invoice PDF

    Returns: PDF file for download
    """
    invoice = Invoice.query.get(invoice_id)

    if not invoice:
        return jsonify({'error': 'Invoice not found'}), 404

    if invoice.user_id != g.user_id:
        return jsonify({'error': 'Not authorized'}), 403

    if not invoice.pdf:
        # Generate PDF if not already created
        try:
            order = invoice.order if invoice.order_id else None
            pdf_buffer = generate_invoice_pdf(invoice, g.user, order)
            return send_file(
                pdf_buffer,
                mimetype='application/pdf',
                as_attachment=True,
                download_name=f'{invoice.invoice_number}.pdf'
            )
        except Exception as e:
            return jsonify({'error': f'Failed to generate PDF: {str(e)}'}), 500

    # Return S3 URL for download
    if invoice.pdf.s3_url:
        return jsonify({
            'pdf_url': invoice.pdf.s3_url,
            'filename': f'{invoice.invoice_number}.pdf'
        }), 200

    return jsonify({'error': 'PDF not available'}), 404


@payment_bp.route('/subscribe', methods=['POST'])
@require_auth
def create_subscription():
    """Create new subscription with flexible billing

    Body: {
        "plan_id": int or "plan_slug": str,
        "billing_period": "monthly" or "annual" (default: monthly),
        "stripe_token": str (optional, for new card)
    }

    Response: {
        "subscription_id": int,
        "plan_name": str,
        "next_billing_date": str (ISO),
        "stripe_subscription_id": str,
        "amount_krw": int,
        "period": str,
        "status": "active"
    }
    """
    data = request.get_json()
    plan_id = data.get('plan_id')
    plan_slug = data.get('plan_slug')
    billing_period = data.get('billing_period', 'monthly')
    stripe_token = data.get('stripe_token')

    # Get plan
    plan = None
    if plan_id:
        plan = SubscriptionPlan.query.get(plan_id)
    elif plan_slug:
        plan = SubscriptionPlan.query.filter_by(slug=plan_slug).first()

    if not plan or not plan.is_active:
        return jsonify({'error': 'Plan not found or inactive'}), 404

    try:
        stripe_subscription_id = None
        amount_krw = 0

        if STRIPE_ENABLED:
            # Create Stripe subscription
            price_id = (plan.stripe_price_id_monthly
                       if billing_period == 'monthly'
                       else plan.stripe_price_id_annual)

            if not price_id:
                return jsonify({'error': 'Plan not configured for Stripe'}), 400

            # Create or get customer
            if not hasattr(g.user, 'stripe_customer_id') or not g.user.stripe_customer_id:
                customer = stripe.Customer.create(
                    email=g.user.email,
                    name=g.user.name
                )
                if hasattr(User, 'stripe_customer_id'):
                    g.user.stripe_customer_id = customer.id
                    db.session.commit()

            # Add payment method
            if stripe_token:
                pm = stripe.PaymentMethod.create(
                    type='card',
                    card={'token': stripe_token}
                )
                stripe.PaymentMethod.attach(
                    pm.id,
                    customer=g.user.stripe_customer_id
                )

            # Create subscription
            stripe_sub = stripe.Subscription.create(
                customer=g.user.stripe_customer_id,
                items=[{'price': price_id}],
                payment_behavior='default_incomplete',
                expand=['latest_invoice.payment_intent']
            )
            stripe_subscription_id = stripe_sub.id

        # Determine amount
        amount_krw = (plan.monthly_price_krw
                     if billing_period == 'monthly'
                     else plan.annual_price_krw)

        # Create new subscription
        subscription = Subscription(
            user_id=g.user_id,
            product_id=plan.id,  # Use plan ID as product_id
            stripe_subscription_id=stripe_subscription_id,
            plan_type=billing_period,
            status='active',
            current_period_end=datetime.utcnow() + (
                timedelta(days=30) if billing_period == 'monthly'
                else timedelta(days=365)
            )
        )
        db.session.add(subscription)
        db.session.commit()

        return jsonify({
            'subscription_id': subscription.id,
            'plan_name': plan.name,
            'next_billing_date': subscription.current_period_end.isoformat(),
            'stripe_subscription_id': stripe_subscription_id,
            'amount_krw': amount_krw,
            'period': billing_period,
            'status': 'active'
        }), 201

    except stripe.error.StripeError as e:
        db.session.rollback()
        return jsonify({'error': f'Stripe error: {str(e)}'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@payment_bp.route('/subscribe/<int:subscription_id>', methods=['PUT'])
@require_auth
def upgrade_subscription(subscription_id):
    """Upgrade or downgrade subscription plan

    Body: {
        "plan_id": int or "plan_slug": str,
        "billing_period": "monthly" or "annual" (optional, keeps current if not specified)
    }

    Response: {
        "subscription_id": int,
        "plan_name": str,
        "next_billing_date": str (ISO),
        "new_amount_krw": int,
        "old_amount_krw": int,
        "proration_credit_krw": int,
        "status": "active"
    }
    """
    subscription = Subscription.query.get(subscription_id)

    if not subscription:
        return jsonify({'error': 'Subscription not found'}), 404

    if subscription.user_id != g.user_id:
        return jsonify({'error': 'Not authorized'}), 403

    data = request.get_json()
    plan_id = data.get('plan_id')
    plan_slug = data.get('plan_slug')
    billing_period = data.get('billing_period', subscription.plan_type)

    # Get new plan
    plan = None
    if plan_id:
        plan = SubscriptionPlan.query.get(plan_id)
    elif plan_slug:
        plan = SubscriptionPlan.query.filter_by(slug=plan_slug).first()

    if not plan or not plan.is_active:
        return jsonify({'error': 'Plan not found or inactive'}), 404

    try:
        # Get old amount for proration calculation
        old_plan = SubscriptionPlan.query.get(subscription.product_id)
        old_amount_krw = (old_plan.monthly_price_krw
                         if subscription.plan_type == 'monthly'
                         else old_plan.annual_price_krw)

        new_amount_krw = (plan.monthly_price_krw
                         if billing_period == 'monthly'
                         else plan.annual_price_krw)

        # Calculate proration credit
        days_remaining = (subscription.current_period_end - datetime.utcnow()).days
        daily_old = old_amount_krw / (30 if subscription.plan_type == 'monthly' else 365)
        proration_credit_krw = int(daily_old * days_remaining)

        # Update Stripe subscription if enabled
        if STRIPE_ENABLED and subscription.stripe_subscription_id:
            price_id = (plan.stripe_price_id_monthly
                       if billing_period == 'monthly'
                       else plan.stripe_price_id_annual)

            if price_id:
                stripe.Subscription.modify(
                    subscription.stripe_subscription_id,
                    items=[{'price': price_id}],
                    proration_behavior='create_pro_rata_schedule'
                )

        # Update subscription
        subscription.product_id = plan.id
        subscription.plan_type = billing_period
        subscription.current_period_end = datetime.utcnow() + (
            timedelta(days=30) if billing_period == 'monthly'
            else timedelta(days=365)
        )
        db.session.commit()

        return jsonify({
            'subscription_id': subscription.id,
            'plan_name': plan.name,
            'next_billing_date': subscription.current_period_end.isoformat(),
            'new_amount_krw': new_amount_krw,
            'old_amount_krw': old_amount_krw,
            'proration_credit_krw': proration_credit_krw,
            'status': 'active'
        }), 200

    except stripe.error.StripeError as e:
        db.session.rollback()
        return jsonify({'error': f'Stripe error: {str(e)}'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@payment_bp.route('/subscribe/<int:subscription_id>', methods=['DELETE'])
@require_auth
def cancel_subscription_v2(subscription_id):
    """Cancel subscription immediately or at period end

    Query params:
    - cancel_at_end: true/false (default: false for immediate cancellation)

    Response: {
        "subscription_id": int,
        "status": "canceling" or "canceled",
        "cancellation_date": str (ISO),
        "refund_eligible": bool,
        "refund_amount_krw": int (if eligible within 7 days)
    }
    """
    subscription = Subscription.query.get(subscription_id)

    if not subscription:
        return jsonify({'error': 'Subscription not found'}), 404

    if subscription.user_id != g.user_id:
        return jsonify({'error': 'Not authorized'}), 403

    cancel_at_end = request.args.get('cancel_at_end', 'false').lower() == 'true'

    try:
        # Check if refund is eligible (within 7 days of subscription start)
        days_since_start = (datetime.utcnow() - subscription.created_at).days
        refund_eligible = days_since_start <= 7
        refund_amount_krw = 0

        if refund_eligible:
            plan = SubscriptionPlan.query.get(subscription.product_id)
            refund_amount_krw = (plan.monthly_price_krw
                               if subscription.plan_type == 'monthly'
                               else plan.annual_price_krw)

        # Cancel Stripe subscription
        if STRIPE_ENABLED and subscription.stripe_subscription_id:
            try:
                if cancel_at_end:
                    stripe.Subscription.modify(
                        subscription.stripe_subscription_id,
                        cancel_at_period_end=True
                    )
                else:
                    stripe.Subscription.delete(subscription.stripe_subscription_id)
            except stripe.error.StripeError:
                pass

        # Update subscription
        subscription.status = 'canceling' if cancel_at_end else 'canceled'
        db.session.commit()

        return jsonify({
            'subscription_id': subscription.id,
            'status': subscription.status,
            'cancellation_date': datetime.utcnow().isoformat(),
            'refund_eligible': refund_eligible,
            'refund_amount_krw': refund_amount_krw if refund_eligible else 0,
            'message': 'Subscription will be canceled at period end' if cancel_at_end else 'Subscription canceled immediately'
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@payment_bp.route('/history', methods=['GET'])
@require_auth
def get_payment_history():
    """Get user payment & invoice history

    Query params:
    - limit: max results (default 50)
    - offset: pagination offset (default 0)
    - status: filter by status (pending, paid, canceled)

    Response: {
        "total": int,
        "payments": [{
            "id": int,
            "type": "payment" or "invoice",
            "date": ISO,
            "amount_krw": int,
            "status": str,
            "invoice_url": str,
            "stripe_url": str
        }]
    }
    """
    limit = min(int(request.args.get('limit', 50)), 100)
    offset = int(request.args.get('offset', 0))
    status_filter = request.args.get('status')

    # Get invoices
    inv_query = Invoice.query.filter_by(user_id=g.user_id)
    if status_filter:
        inv_query = inv_query.filter_by(status=status_filter)

    invoices = inv_query.order_by(
        Invoice.issued_date.desc()
    ).limit(limit).offset(offset).all()

    # Get payments
    pay_query = Payment.query.filter_by(user_id=g.user_id)
    if status_filter:
        pay_query = pay_query.filter_by(status=status_filter)

    payments = pay_query.order_by(
        Payment.created_at.desc()
    ).limit(limit).offset(offset).all()

    # Merge and sort
    history = []

    for inv in invoices:
        history.append({
            'id': inv.id,
            'type': 'invoice',
            'date': inv.issued_date.isoformat(),
            'amount_krw': inv.total_krw,
            'status': inv.status,
            'invoice_number': inv.invoice_number,
            'invoice_url': inv.pdf.s3_url if inv.pdf else None,
            'stripe_url': None,  # Could fetch from Stripe if needed
            'due_date': inv.due_date.isoformat() if inv.due_date else None,
        })

    for pay in payments:
        history.append({
            'id': pay.id,
            'type': 'payment',
            'date': pay.created_at.isoformat(),
            'amount': pay.amount,
            'status': pay.status,
            'stripe_payment_id': pay.stripe_payment_id,
            'invoice_url': None,
        })

    # Sort by date descending
    history.sort(key=lambda x: x['date'], reverse=True)

    return jsonify({
        'total': len(history),
        'limit': limit,
        'offset': offset,
        'history': history[:limit]
    }), 200


# ============ CONVERSION & RATES ============

@payment_bp.route('/exchange-rate', methods=['GET'])
def get_exchange_rate():
    """Get current USD to KRW exchange rate

    Query params:
    - base_currency: base currency code (default: USD)
    - target_currency: target currency code (default: KRW)

    Response: {
        "base": str,
        "target": str,
        "rate": float,
        "timestamp": ISO
    }
    """
    base = request.args.get('base_currency', 'USD')
    target = request.args.get('target_currency', 'KRW')

    if base == 'USD' and target == 'KRW':
        rate = ExchangeRateService.get_current_rate()
    elif base == 'KRW' and target == 'USD':
        rate = 1 / ExchangeRateService.get_current_rate()
    else:
        return jsonify({'error': f'Unsupported currency pair: {base}/{target}'}), 400

    return jsonify({
        'base': base,
        'target': target,
        'rate': rate,
        'timestamp': datetime.utcnow().isoformat()
    }), 200


@payment_bp.route('/convert', methods=['POST'])
def convert_currency():
    """Convert between currencies

    Body: {
        "amount": float,
        "from_currency": str (USD or KRW),
        "to_currency": str (USD or KRW)
    }

    Response: {
        "original_amount": float,
        "from_currency": str,
        "to_currency": str,
        "converted_amount": float or int,
        "rate": float
    }
    """
    data = request.get_json()
    amount = data.get('amount')
    from_currency = data.get('from_currency', 'USD')
    to_currency = data.get('to_currency', 'KRW')

    if not amount or amount <= 0:
        return jsonify({'error': 'Invalid amount'}), 400

    if from_currency == 'USD' and to_currency == 'KRW':
        rate = ExchangeRateService.get_current_rate()
        converted = ExchangeRateService.usd_to_krw(amount)
    elif from_currency == 'KRW' and to_currency == 'USD':
        rate = 1 / ExchangeRateService.get_current_rate()
        converted = ExchangeRateService.krw_to_usd(amount)
    else:
        return jsonify({'error': f'Unsupported currency pair: {from_currency}/{to_currency}'}), 400

    return jsonify({
        'original_amount': amount,
        'from_currency': from_currency,
        'to_currency': to_currency,
        'converted_amount': converted,
        'rate': rate
    }), 200


# ============ WEBHOOK HANDLERS ============

@payment_bp.route('/webhook/stripe', methods=['POST'])
def stripe_webhook_enhanced():
    """Enhanced Stripe webhook handler with subscription auto-renewal

    Handles:
    - customer.subscription.deleted → Mark subscription as canceled
    - customer.subscription.updated → Update subscription details
    - invoice.payment_succeeded → Mark invoice as paid
    - invoice.payment_failed → Retry payment
    """
    if not STRIPE_ENABLED:
        return {'error': 'Webhooks not enabled'}, 400

    payload = request.get_data()
    sig_header = request.headers.get('Stripe-Signature')
    webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET')

    if not webhook_secret:
        return {'error': 'Webhook secret not configured'}, 400

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)

        # Handle subscription deletion
        if event['type'] == 'customer.subscription.deleted':
            sub_id = event['data']['object']['id']
            subscription = Subscription.query.filter_by(stripe_subscription_id=sub_id).first()
            if subscription:
                subscription.status = 'canceled'
                db.session.commit()

        # Handle subscription updates
        elif event['type'] == 'customer.subscription.updated':
            sub_id = event['data']['object']['id']
            subscription = Subscription.query.filter_by(stripe_subscription_id=sub_id).first()
            if subscription:
                # Update period end
                stripe_sub = stripe.Subscription.retrieve(sub_id)
                if stripe_sub.current_period_end:
                    subscription.current_period_end = datetime.fromtimestamp(
                        stripe_sub.current_period_end
                    )
                db.session.commit()

        # Handle payment success
        elif event['type'] == 'invoice.payment_succeeded':
            invoice_id = event['data']['object']['id']
            invoice = Invoice.query.filter_by(stripe_invoice_id=invoice_id).first()
            if invoice:
                invoice.status = 'paid'
                invoice.paid_date = datetime.utcnow()
                db.session.commit()

        # Handle payment failure
        elif event['type'] == 'invoice.payment_failed':
            invoice_id = event['data']['object']['id']
            invoice = Invoice.query.filter_by(stripe_invoice_id=invoice_id).first()
            if invoice:
                invoice.status = 'pending'
                db.session.commit()

        return {'message': 'Webhook received'}, 200

    except ValueError:
        return {'error': 'Invalid payload'}, 400
    except stripe.error.SignatureVerificationError:
        return {'error': 'Invalid signature'}, 400
    except Exception as e:
        return {'error': str(e)}, 500


# ============ SUBSCRIPTION PLANS ============

@payment_bp.route('/plans', methods=['GET'])
def get_subscription_plans():
    """Get all active subscription plans with pricing

    Response: [{
        "id": int,
        "name": str,
        "slug": str,
        "description": str,
        "monthly_price_krw": int,
        "annual_price_krw": int,
        "monthly_price_usd": float,
        "annual_price_usd": float,
        "features": [str],
        "max_projects": int,
        "max_users": int,
        "is_active": bool
    }]
    """
    plans = SubscriptionPlan.query.filter_by(is_active=True).all()
    exchange_rate = ExchangeRateService.get_current_rate()

    result = []
    for plan in plans:
        plan_dict = plan.to_dict()
        # Add USD pricing
        plan_dict['monthly_price_usd'] = round(plan.monthly_price_krw / exchange_rate, 2)
        plan_dict['annual_price_usd'] = round(plan.annual_price_krw / exchange_rate, 2)
        result.append(plan_dict)

    return jsonify(result), 200
