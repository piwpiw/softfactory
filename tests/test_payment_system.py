"""Test Suite for Payment System v2.0 — File Storage + Invoices + Subscriptions"""
import pytest
import json
from datetime import datetime, timedelta
from backend.models import (
    db, User, Invoice, Order, SubscriptionPlan,
    FileUpload, Subscription, Payment
)


class TestFileUpload:
    """Test S3 file upload functionality"""

    def test_upload_file_success(self, client, auth_token):
        """Test successful file upload"""
        with open('tests/fixtures/sample.pdf', 'rb') as f:
            response = client.post(
                '/api/files/upload',
                data={'file': f},
                headers={'Authorization': f'Bearer {auth_token}'},
                content_type='multipart/form-data'
            )

        assert response.status_code == 201
        data = response.get_json()
        assert 'file_id' in data
        assert 'cdn_url' in data
        assert data['category'] == 'document'
        assert data['original_filename'] == 'sample.pdf'

    def test_upload_invalid_type(self, client, auth_token):
        """Test rejection of invalid file type"""
        with open('tests/fixtures/malware.exe', 'rb') as f:
            response = client.post(
                '/api/files/upload',
                data={'file': f},
                headers={'Authorization': f'Bearer {auth_token}'},
                content_type='multipart/form-data'
            )

        assert response.status_code == 400
        data = response.get_json()
        assert 'not allowed' in data['error'].lower()

    def test_upload_oversized_file(self, client, auth_token):
        """Test rejection of files > 50MB"""
        # Create a mock >50MB file
        response = client.post(
            '/api/files/upload',
            data={'file': (b'x' * 51 * 1024 * 1024, 'bigfile.zip')},
            headers={'Authorization': f'Bearer {auth_token}'},
            content_type='multipart/form-data'
        )

        assert response.status_code == 400
        data = response.get_json()
        assert 'exceeds' in data['error'].lower()

    def test_list_user_files(self, client, auth_token, test_user):
        """Test listing user files with pagination"""
        # Upload 3 files
        for i in range(3):
            client.post(
                '/api/files/upload',
                data={'file': (b'test', f'file{i}.txt')},
                headers={'Authorization': f'Bearer {auth_token}'},
                content_type='multipart/form-data'
            )

        response = client.get(
            '/api/files?limit=10&offset=0',
            headers={'Authorization': f'Bearer {auth_token}'}
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data['total'] >= 3
        assert len(data['files']) >= 3

    def test_presigned_url(self, client, auth_token, test_user):
        """Test presigned URL generation"""
        # Upload a file first
        upload_response = client.post(
            '/api/files/upload',
            data={'file': (b'test', 'file.pdf')},
            headers={'Authorization': f'Bearer {auth_token}'},
            content_type='multipart/form-data'
        )
        file_id = upload_response.get_json()['file_id']

        # Get presigned URL
        response = client.post(
            '/api/files/presigned-url',
            json={'file_id': file_id, 'expiration_hours': 24},
            headers={'Authorization': f'Bearer {auth_token}'}
        )

        assert response.status_code == 200
        data = response.get_json()
        assert 'presigned_url' in data
        assert 'expires_at' in data

    def test_delete_file(self, client, auth_token, test_user):
        """Test file deletion"""
        # Upload a file
        upload_response = client.post(
            '/api/files/upload',
            data={'file': (b'test', 'temp.txt')},
            headers={'Authorization': f'Bearer {auth_token}'},
            content_type='multipart/form-data'
        )
        file_id = upload_response.get_json()['file_id']

        # Delete it
        response = client.delete(
            f'/api/files/{file_id}',
            headers={'Authorization': f'Bearer {auth_token}'}
        )

        assert response.status_code == 200

        # Verify deletion
        get_response = client.get(
            f'/api/files/{file_id}',
            headers={'Authorization': f'Bearer {auth_token}'}
        )
        assert get_response.status_code == 404


class TestInvoicing:
    """Test invoice generation and management"""

    def test_create_invoice(self, client, auth_token, test_user):
        """Test invoice creation with PDF generation"""
        response = client.post(
            '/api/payment/invoice',
            json={
                'amount_krw': 99000,
                'tax_krw': 9900,
                'due_days': 30
            },
            headers={'Authorization': f'Bearer {auth_token}'}
        )

        assert response.status_code == 201
        data = response.get_json()
        assert 'invoice_id' in data
        assert 'invoice_number' in data
        assert data['total_krw'] == 108900
        assert data['invoice_number'].startswith('202602')  # YYYYMMDD format

    def test_invoice_with_order(self, client, auth_token, test_user):
        """Test invoice linked to order"""
        # Create order first
        order = Order(
            user_id=test_user.id,
            order_number='ORD-001',
            items_json='[{"product_id": 1, "quantity": 1, "price_krw": 99000}]',
            subtotal_krw=99000,
            tax_krw=9900,
            total_amount_krw=108900
        )
        db.session.add(order)
        db.session.commit()

        # Create invoice for order
        response = client.post(
            '/api/payment/invoice',
            json={
                'order_id': order.id,
                'amount_krw': 99000,
                'tax_krw': 9900
            },
            headers={'Authorization': f'Bearer {auth_token}'}
        )

        assert response.status_code == 201
        data = response.get_json()
        assert data['invoice_id'] is not None

    def test_invoice_pdf_upload(self, client, auth_token, test_user):
        """Test that invoice PDF is uploaded to S3"""
        response = client.post(
            '/api/payment/invoice',
            json={'amount_krw': 50000, 'tax_krw': 5000},
            headers={'Authorization': f'Bearer {auth_token}'}
        )

        assert response.status_code == 201
        data = response.get_json()

        # Verify PDF was created
        invoice = Invoice.query.get(data['invoice_id'])
        assert invoice.pdf_file_id is not None
        assert invoice.pdf is not None


class TestSubscriptions:
    """Test subscription management"""

    def setup_method(self):
        """Create test subscription plans"""
        plans = [
            SubscriptionPlan(
                name='Starter',
                slug='starter-monthly',
                monthly_price_krw=9900,
                annual_price_krw=99000,
                stripe_price_id_monthly='price_starter_monthly',
                stripe_price_id_annual='price_starter_annual',
                features_json=json.dumps(['5 projects', 'Basic support']),
                max_projects=5,
                max_users=3,
                is_active=True
            ),
            SubscriptionPlan(
                name='Pro',
                slug='pro-monthly',
                monthly_price_krw=29900,
                annual_price_krw=299000,
                stripe_price_id_monthly='price_pro_monthly',
                stripe_price_id_annual='price_pro_annual',
                features_json=json.dumps(['Unlimited projects', 'Priority support']),
                is_active=True
            ),
        ]
        for plan in plans:
            db.session.add(plan)
        db.session.commit()

    def test_get_subscription_plans(self, client):
        """Test retrieving available plans"""
        response = client.get('/api/payment/plans')

        assert response.status_code == 200
        data = response.get_json()
        assert len(data) >= 2
        assert data[0]['slug'] in ['starter-monthly', 'pro-monthly']
        assert 'features' in data[0]
        assert 'monthly_price_krw' in data[0]

    def test_create_subscription(self, client, auth_token, test_user):
        """Test subscription creation"""
        response = client.post(
            '/api/payment/subscribe',
            json={
                'plan_slug': 'pro-monthly',
                'billing_period': 'monthly'
            },
            headers={'Authorization': f'Bearer {auth_token}'}
        )

        assert response.status_code == 201
        data = response.get_json()
        assert 'subscription_id' in data
        assert data['amount_krw'] == 29900
        assert data['period'] == 'monthly'
        assert data['status'] == 'active'

    def test_subscription_upgrade(self, client, auth_token, test_user):
        """Test upgrading from Starter to Pro"""
        # Subscribe to Starter
        client.post(
            '/api/payment/subscribe',
            json={'plan_slug': 'starter-monthly', 'billing_period': 'monthly'},
            headers={'Authorization': f'Bearer {auth_token}'}
        )

        # Upgrade to Pro (old subscription should be canceled)
        response = client.post(
            '/api/payment/subscribe',
            json={'plan_slug': 'pro-monthly', 'billing_period': 'monthly'},
            headers={'Authorization': f'Bearer {auth_token}'}
        )

        assert response.status_code == 201
        data = response.get_json()
        assert data['amount_krw'] == 29900

        # Verify only one active subscription
        active_subs = Subscription.query.filter_by(
            user_id=test_user.id,
            status='active'
        ).all()
        assert len(active_subs) == 1

    def test_annual_subscription(self, client, auth_token, test_user):
        """Test annual billing"""
        response = client.post(
            '/api/payment/subscribe',
            json={'plan_slug': 'pro-monthly', 'billing_period': 'annual'},
            headers={'Authorization': f'Bearer {auth_token}'}
        )

        assert response.status_code == 201
        data = response.get_json()
        assert data['amount_krw'] == 299000  # Annual price
        assert data['period'] == 'annual'


class TestPaymentHistory:
    """Test payment history and reconciliation"""

    def test_get_payment_history(self, client, auth_token, test_user):
        """Test retrieving payment history"""
        # Create some test invoices
        for i in range(3):
            invoice = Invoice(
                user_id=test_user.id,
                invoice_number=f'2026022{6+i}-000{i+1}',
                amount_krw=50000,
                tax_krw=5000,
                total_krw=55000,
                status='paid' if i < 2 else 'pending'
            )
            db.session.add(invoice)
        db.session.commit()

        response = client.get(
            '/api/payment/history?limit=10&offset=0',
            headers={'Authorization': f'Bearer {auth_token}'}
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data['total'] >= 3
        assert any(item['type'] == 'invoice' for item in data['history'])

    def test_filter_history_by_status(self, client, auth_token, test_user):
        """Test filtering history by payment status"""
        response = client.get(
            '/api/payment/history?status=paid',
            headers={'Authorization': f'Bearer {auth_token}'}
        )

        assert response.status_code == 200
        data = response.get_json()
        for item in data['history']:
            assert item.get('status') == 'paid'


class TestModels:
    """Test database models and relationships"""

    def test_file_upload_model(self, test_user):
        """Test FileUpload model creation"""
        upload = FileUpload(
            user_id=test_user.id,
            file_key='uploads/123/test.pdf',
            original_filename='test.pdf',
            file_size=1024,
            content_type='application/pdf',
            category='document',
            s3_url='https://bucket.s3.amazonaws.com/uploads/123/test.pdf',
            cdn_url='https://cdn.example.com/uploads/123/test.pdf'
        )
        db.session.add(upload)
        db.session.commit()

        assert upload.id is not None
        assert upload.user_id == test_user.id
        assert upload.category == 'document'

    def test_order_model(self, test_user):
        """Test Order model creation"""
        order = Order(
            user_id=test_user.id,
            order_number='ORD-001',
            items_json='[{"product_id": 1, "quantity": 2, "price_krw": 50000}]',
            subtotal_krw=100000,
            tax_krw=10000,
            total_amount_krw=110000
        )
        db.session.add(order)
        db.session.commit()

        assert order.id is not None
        assert order.order_number == 'ORD-001'
        assert order.total_amount_krw == 110000

    def test_invoice_model(self, test_user):
        """Test Invoice model creation"""
        invoice = Invoice(
            user_id=test_user.id,
            invoice_number='20260226-0001',
            amount_krw=99000,
            tax_krw=9900,
            total_krw=108900,
            status='issued'
        )
        db.session.add(invoice)
        db.session.commit()

        assert invoice.id is not None
        assert invoice.invoice_number == '20260226-0001'
        assert invoice.status == 'issued'
        assert invoice.paid_date is None


@pytest.fixture
def auth_token(client, test_user):
    """Generate JWT token for test user"""
    response = client.post(
        '/api/auth/login',
        json={'email': test_user.email, 'password': 'TestPassword123!'}
    )
    return response.get_json()['token']


@pytest.fixture
def test_user(app):
    """Create test user"""
    with app.app_context():
        user = User(
            email='payment-test@example.com',
            name='Payment Test User',
            password_hash='hashed_password',
            email_verified=True
        )
        db.session.add(user)
        db.session.commit()
        return user
