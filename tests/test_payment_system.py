"""Test Suite for Payment System v2.0 ??File Storage + Invoices + Subscriptions"""

import io
import json
from datetime import datetime

import pytest

from backend.models import (
    Invoice,
    Order,
    Payment,
    Subscription,
    SubscriptionPlan,
    db,
)


class _FakeS3Client:
    def put_object(self, **kwargs):
        return {"ok": True, "key": kwargs.get("Key")}

    def delete_object(self, **kwargs):
        return {"ok": True, "key": kwargs.get("Key")}

    def generate_presigned_url(self, operation, Params=None, ExpiresIn=None):
        key = (Params or {}).get("Key", "unknown")
        return f"https://example.test/presigned/{key}?expires={ExpiresIn or 0}"


@pytest.fixture
def fake_s3(monkeypatch):
    """Run file and invoice tests against a stubbed storage backend."""
    from backend import payment
    from backend.services import file_service

    fake_client = _FakeS3Client()
    monkeypatch.setattr(file_service, "S3_ENABLED", True)
    monkeypatch.setattr(file_service, "get_s3_client", lambda: fake_client)
    monkeypatch.setattr(payment, "get_s3_client", lambda: fake_client)
    return fake_client


def _multipart_file(content: bytes, filename: str, content_type: str):
    return (io.BytesIO(content), filename, content_type)


class TestFileUpload:
    """Test S3 file upload functionality."""

    def test_upload_file_success(self, client, auth_token, fake_s3):
        response = client.post(
            "/api/files/upload",
            data={"file": _multipart_file(b"%PDF-1.4 test document", "sample.pdf", "application/pdf")},
            headers={"Authorization": f"Bearer {auth_token}"},
            content_type="multipart/form-data",
        )

        assert response.status_code == 201
        data = response.get_json()
        assert "file_id" in data
        assert "cdn_url" in data
        assert data["category"] == "document"
        assert data["original_filename"] == "sample.pdf"

    def test_upload_invalid_type(self, client, auth_token, fake_s3):
        response = client.post(
            "/api/files/upload",
            data={"file": _multipart_file(b"MZ executable payload", "malware.exe", "application/octet-stream")},
            headers={"Authorization": f"Bearer {auth_token}"},
            content_type="multipart/form-data",
        )

        assert response.status_code == 400
        data = response.get_json()
        assert "not allowed" in data["error"].lower()

    def test_upload_oversized_file(self, client, auth_token, fake_s3):
        response = client.post(
            "/api/files/upload",
            data={"file": _multipart_file(b"x" * 51 * 1024 * 1024, "bigfile.pdf", "application/pdf")},
            headers={"Authorization": f"Bearer {auth_token}"},
            content_type="multipart/form-data",
        )

        assert response.status_code == 400
        data = response.get_json()
        assert "exceeds" in data["error"].lower()

    def test_list_user_files(self, client, auth_token, fake_s3):
        for i in range(3):
            client.post(
                "/api/files/upload",
                data={"file": _multipart_file(b"test", f"file{i}.pdf", "application/pdf")},
                headers={"Authorization": f"Bearer {auth_token}"},
                content_type="multipart/form-data",
            )

        response = client.get(
            "/api/files?limit=10&offset=0",
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["total"] >= 3
        assert len(data["files"]) >= 3

    def test_presigned_url(self, client, auth_token, fake_s3):
        upload_response = client.post(
            "/api/files/upload",
            data={"file": _multipart_file(b"test", "file.pdf", "application/pdf")},
            headers={"Authorization": f"Bearer {auth_token}"},
            content_type="multipart/form-data",
        )
        file_id = upload_response.get_json()["file_id"]

        response = client.post(
            "/api/files/presigned-url",
            json={"file_id": file_id, "expiration_hours": 24},
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 200
        data = response.get_json()
        assert "presigned_url" in data
        assert "expires_at" in data

    def test_delete_file(self, client, auth_token, fake_s3):
        upload_response = client.post(
            "/api/files/upload",
            data={"file": _multipart_file(b"test", "temp.pdf", "application/pdf")},
            headers={"Authorization": f"Bearer {auth_token}"},
            content_type="multipart/form-data",
        )
        file_id = upload_response.get_json()["file_id"]

        response = client.delete(
            f"/api/files/{file_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 200

        get_response = client.get(
            f"/api/files/{file_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert get_response.status_code == 404


class TestInvoicing:
    """Test invoice generation and management."""

    def test_create_invoice(self, client, auth_token, fake_s3):
        response = client.post(
            "/api/payment/invoice",
            json={"amount_krw": 99000, "tax_krw": 9900, "due_days": 30},
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 201
        data = response.get_json()
        assert "invoice_id" in data
        assert "invoice_number" in data
        assert data["total_krw"] == 108900
        assert data["invoice_number"].startswith(datetime.utcnow().strftime("%Y%m%d"))

    def test_invoice_with_order(self, client, auth_token, test_user, fake_s3):
        order = Order(
            user_id=test_user.id,
            order_number="ORD-001",
            items_json='[{"product_id": 1, "quantity": 1, "price_krw": 99000}]',
            subtotal_krw=99000,
            tax_krw=9900,
            total_amount_krw=108900,
        )
        db.session.add(order)
        db.session.commit()

        response = client.post(
            "/api/payment/invoice",
            json={"order_id": order.id, "amount_krw": 99000, "tax_krw": 9900},
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 201
        data = response.get_json()
        assert data["invoice_id"] is not None

    def test_invoice_pdf_upload(self, client, auth_token, fake_s3):
        response = client.post(
            "/api/payment/invoice",
            json={"amount_krw": 50000, "tax_krw": 5000},
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 201
        data = response.get_json()

        invoice = Invoice.query.get(data["invoice_id"])
        assert invoice.pdf_file_id is not None
        assert invoice.pdf is not None


class TestSubscriptions:
    """Test subscription management."""

    @staticmethod
    def _seed_plans():
        plans = [
            SubscriptionPlan(
                name="Starter",
                slug="starter-monthly",
                monthly_price_krw=9900,
                annual_price_krw=99000,
                stripe_price_id_monthly="price_starter_monthly",
                stripe_price_id_annual="price_starter_annual",
                features_json=json.dumps(["5 projects", "Basic support"]),
                max_projects=5,
                max_users=3,
                is_active=True,
            ),
            SubscriptionPlan(
                name="Pro",
                slug="pro-monthly",
                monthly_price_krw=29900,
                annual_price_krw=299000,
                stripe_price_id_monthly="price_pro_monthly",
                stripe_price_id_annual="price_pro_annual",
                features_json=json.dumps(["Unlimited projects", "Priority support"]),
                is_active=True,
            ),
        ]
        for plan in plans:
            db.session.add(plan)
        db.session.commit()
        return plans

    def test_get_subscription_plans(self, client):
        self._seed_plans()
        response = client.get("/api/payment/plans")

        assert response.status_code == 200
        data = response.get_json()
        assert len(data) >= 2
        assert data[0]["slug"] in ["starter-monthly", "pro-monthly"]
        assert "features" in data[0]
        assert "monthly_price_krw" in data[0]

    def test_create_subscription(self, client, auth_token):
        self._seed_plans()
        response = client.post(
            "/api/payment/subscribe",
            json={"plan_slug": "pro-monthly", "billing_period": "monthly"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 201
        data = response.get_json()
        assert "subscription_id" in data
        assert data["amount_krw"] == 29900
        assert data["period"] == "monthly"
        assert data["status"] == "active"

    def test_subscription_upgrade(self, client, auth_token):
        self._seed_plans()
        client.post(
            "/api/payment/subscribe",
            json={"plan_slug": "starter-monthly", "billing_period": "monthly"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        response = client.post(
            "/api/payment/subscribe",
            json={"plan_slug": "pro-monthly", "billing_period": "monthly"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 201
        data = response.get_json()
        assert data["amount_krw"] == 29900

        active_subs = Subscription.query.filter_by(user_id=1, status="active").all()
        assert len(active_subs) == 1

    def test_annual_subscription(self, client, auth_token):
        self._seed_plans()
        response = client.post(
            "/api/payment/subscribe",
            json={"plan_slug": "pro-monthly", "billing_period": "annual"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 201
        data = response.get_json()
        assert data["amount_krw"] == 299000
        assert data["period"] == "annual"


class TestPaymentHistory:
    """Test payment history and reconciliation."""

    def test_get_payment_history(self, client, auth_token, test_user):
        for i in range(3):
            invoice = Invoice(
                user_id=test_user.id,
                invoice_number=f"2026022{6 + i}-000{i + 1}",
                amount_krw=50000,
                tax_krw=5000,
                total_krw=55000,
                status="paid" if i < 2 else "pending",
            )
            db.session.add(invoice)
        db.session.commit()

        response = client.get(
            "/api/payment/history?limit=10&offset=0",
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["total"] >= 3
        assert any(item["type"] == "invoice" for item in data["history"])

    def test_filter_history_by_status(self, client, auth_token):
        response = client.get(
            "/api/payment/history?status=paid",
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 200
        data = response.get_json()
        for item in data["history"]:
            assert item.get("status") == "paid"
