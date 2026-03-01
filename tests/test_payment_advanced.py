"""Comprehensive Payment System Tests — KRW, Invoices, Subscriptions"""
import pytest
from datetime import datetime, timedelta


class TestExchangeRateService:
    """Test exchange rate conversion utilities"""

    def test_get_current_rate(self):
        """Test fetching current exchange rate"""
        from backend.payment import ExchangeRateService
        rate = ExchangeRateService.get_current_rate()
        assert isinstance(rate, (int, float))
        assert rate > 1000

    def test_usd_to_krw_conversion(self):
        """Test USD to KRW conversion"""
        from backend.payment import ExchangeRateService
        usd = 100
        krw = ExchangeRateService.usd_to_krw(usd)
        assert isinstance(krw, int)
        assert krw > 100000

    def test_krw_to_usd_conversion(self):
        """Test KRW to USD conversion"""
        from backend.payment import ExchangeRateService
        krw = 100000
        usd = ExchangeRateService.krw_to_usd(krw)
        assert isinstance(usd, float)
        assert usd > 0

    def test_bidirectional_conversion(self):
        """Test bidirectional conversion consistency"""
        from backend.payment import ExchangeRateService
        original_usd = 100
        krw = ExchangeRateService.usd_to_krw(original_usd)
        back_to_usd = ExchangeRateService.krw_to_usd(krw)
        assert abs(back_to_usd - original_usd) < 1


class TestTaxCalculation:
    """Test tax calculation utilities"""

    def test_default_10_percent_vat(self):
        """Test 10% VAT calculation (Korean standard)"""
        from backend.payment import calculate_tax
        amount = 100000
        tax = calculate_tax(amount)
        assert tax == 10000

    def test_custom_tax_rate(self):
        """Test custom tax rate"""
        from backend.payment import calculate_tax
        amount = 100000
        tax = calculate_tax(amount, tax_rate=0.08)
        assert tax == 8000

    def test_zero_amount(self):
        """Test zero amount"""
        from backend.payment import calculate_tax
        tax = calculate_tax(0)
        assert tax == 0

    def test_large_amount(self):
        """Test large amount"""
        from backend.payment import calculate_tax
        amount = 10000000
        tax = calculate_tax(amount)
        assert tax == 1000000


class TestNumberGeneration:
    """Test invoice and shipping number generation"""

    def test_invoice_number_format(self):
        """Test invoice number format YYYYMMDD-XXXX"""
        from backend.payment import generate_invoice_number
        number = generate_invoice_number()
        parts = number.split('-')
        assert len(parts) == 2
        assert len(parts[0]) == 8
        assert len(parts[1]) == 4
        assert parts[0].isdigit()
        assert parts[1].isdigit()

    def test_shipping_number_format(self):
        """Test shipping number format YYYYMMDD-XXXX"""
        from backend.payment import generate_shipping_number
        number = generate_shipping_number()
        parts = number.split('-')
        assert len(parts) == 2
        assert len(parts[0]) == 8
        assert len(parts[1]) == 4


class TestPaymentEndpoints:
    """Test payment API endpoints"""

    def test_get_exchange_rate_endpoint(self, client):
        """Test exchange rate endpoint"""
        response = client.get('/api/payment/exchange-rate')
        assert response.status_code == 200
        data = response.get_json()
        assert data['base'] == 'USD'
        assert data['target'] == 'KRW'
        assert data['rate'] > 1000

    def test_currency_conversion_endpoint(self, client):
        """Test currency conversion endpoint"""
        response = client.post('/api/payment/convert', json={
            'amount': 100,
            'from_currency': 'USD',
            'to_currency': 'KRW'
        })
        assert response.status_code == 200
        data = response.get_json()
        assert data['converted_amount'] > 100000

    def test_subscription_plans_endpoint(self, client):
        """Test subscription plans endpoint"""
        response = client.get('/api/payment/plans')
        assert response.status_code == 200
        plans = response.get_json()
        assert isinstance(plans, list)
        for plan in plans:
            assert 'monthly_price_krw' in plan
            assert 'monthly_price_usd' in plan


class TestInvoiceAPI:
    """Test invoice creation and retrieval"""

    def test_create_invoice_authenticated(self, client, user_headers):
        """Test creating invoice with authentication"""
        response = client.post('/api/payment/invoice', headers=user_headers, json={
            'amount_krw': 100000,
            'tax_rate': 0.10,
            'due_days': 30
        })
        assert response.status_code == 201
        data = response.get_json()
        assert 'invoice_id' in data
        assert 'invoice_number' in data
        assert data['total_krw'] == 110000

    def test_create_invoice_invalid_amount(self, client, user_headers):
        """Test invalid invoice amount"""
        response = client.post('/api/payment/invoice', headers=user_headers, json={
            'amount_krw': 0
        })
        assert response.status_code == 400


class TestSubscriptionAPI:
    """Test subscription management endpoints"""

    def test_get_subscription_plans(self, client):
        """Test getting subscription plans"""
        response = client.get('/api/payment/plans')
        assert response.status_code == 200

    def test_get_subscriptions_authenticated(self, client, user_headers):
        """Test getting user subscriptions"""
        response = client.get('/api/payment/subscriptions', headers=user_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert 'subscriptions' in data


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
