"""
Encryption & API Key Management Tests

Coverage:
- EncryptionService: encrypt/decrypt performance
- EncryptedString TypeDecorator
- API key lifecycle (create, list, revoke)
- Audit logging
- Key rotation scenarios
"""
import pytest
import time
from datetime import datetime, timedelta
from cryptography.fernet import Fernet, InvalidToken

from backend.app import create_app, db
from backend.models import User, APIKey, AuditLog, EncryptionKeyRotation
from backend.encryption_service import encryption_service
from backend.types import EncryptedString


@pytest.fixture
def app():
    """Create test app with test database"""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture
def test_user(app):
    """Create test user"""
    with app.app_context():
        user = User(
            email='test@example.com',
            password_hash='hashed_password',
            name='Test User',
            role='admin'
        )
        db.session.add(user)
        db.session.commit()
        return user


# ============ ENCRYPTION SERVICE TESTS ============

class TestEncryptionService:
    """Test encryption service functionality"""

    def test_encrypt_decrypt_string(self):
        """Test basic encrypt/decrypt"""
        original = "sensitive@data.com"
        encrypted = encryption_service.encrypt_field(original)

        assert encrypted != original
        assert isinstance(encrypted, str)

        decrypted = encryption_service.decrypt_field(encrypted)
        assert decrypted == original

    def test_encrypt_none_returns_none(self):
        """Test that encrypting None returns None"""
        result = encryption_service.encrypt_field(None)
        assert result is None

    def test_decrypt_none_returns_none(self):
        """Test that decrypting None returns None"""
        result = encryption_service.decrypt_field(None)
        assert result is None

    def test_decrypt_invalid_token_raises_error(self):
        """Test that decrypting invalid token raises ValueError"""
        with pytest.raises(ValueError, match='Invalid token'):
            encryption_service.decrypt_field("invalid_token_here")

    def test_encryption_performance(self):
        """Encryption should be < 1ms per field"""
        data = "test_data_" * 10

        start = time.perf_counter()
        for _ in range(100):
            encryption_service.encrypt_field(data)
        elapsed = time.perf_counter() - start

        avg_time = (elapsed / 100) * 1000  # Convert to ms
        assert avg_time < 1.0, f"Encryption too slow: {avg_time}ms"

    def test_decryption_performance(self):
        """Decryption should be < 1ms per field"""
        encrypted = encryption_service.encrypt_field("test_data")

        start = time.perf_counter()
        for _ in range(100):
            encryption_service.decrypt_field(encrypted)
        elapsed = time.perf_counter() - start

        avg_time = (elapsed / 100) * 1000  # Convert to ms
        assert avg_time < 1.0, f"Decryption too slow: {avg_time}ms"

    def test_unicode_encryption(self):
        """Test encryption of unicode characters"""
        original = "한글 테스트 🔐 特殊文字"
        encrypted = encryption_service.encrypt_field(original)
        decrypted = encryption_service.decrypt_field(encrypted)
        assert decrypted == original

    def test_large_text_encryption(self):
        """Test encryption of large text"""
        original = "x" * 10000
        encrypted = encryption_service.encrypt_field(original)
        decrypted = encryption_service.decrypt_field(encrypted)
        assert decrypted == original


# ============ API KEY LIFECYCLE TESTS ============

class TestAPIKeyManagement:
    """Test API key creation, listing, revocation"""

    def test_create_api_key(self, client, app, test_user):
        """Test creating a new API key"""
        with app.app_context():
            # Login
            from backend.auth import create_jwt_token
            token = create_jwt_token(test_user.id, test_user.email, test_user.role)

            response = client.post(
                '/api/encryption/keys',
                json={
                    'name': 'Production API Key',
                    'expires_in_days': 30,
                    'scopes': 'read:projects,write:sns'
                },
                headers={'Authorization': f'Bearer {token}'}
            )

            assert response.status_code == 201
            data = response.get_json()
            assert data['name'] == 'Production API Key'
            assert 'key' in data
            assert 'prefix' in data
            assert len(data['key']) > 32
            assert data['key'].startswith('pk_')

    def test_create_api_key_invalid_name(self, client, app, test_user):
        """Test creating API key with invalid name"""
        with app.app_context():
            from backend.auth import create_jwt_token
            token = create_jwt_token(test_user.id, test_user.email, test_user.role)

            response = client.post(
                '/api/encryption/keys',
                json={
                    'name': '',  # Empty name
                    'expires_in_days': 30
                },
                headers={'Authorization': f'Bearer {token}'}
            )

            assert response.status_code == 400
            assert 'Invalid key name' in response.get_json()['error']

    def test_list_api_keys(self, client, app, test_user):
        """Test listing API keys"""
        with app.app_context():
            # Create two keys
            key1 = APIKey(
                user_id=test_user.id,
                name='Key 1',
                prefix='pk_aaa111',
                encrypted_key=encryption_service.encrypt_field('secret1'),
                expires_at=datetime.utcnow() + timedelta(days=30)
            )
            key2 = APIKey(
                user_id=test_user.id,
                name='Key 2',
                prefix='pk_bbb222',
                encrypted_key=encryption_service.encrypt_field('secret2'),
                expires_at=datetime.utcnow() + timedelta(days=60)
            )
            db.session.add_all([key1, key2])
            db.session.commit()

            from backend.auth import create_jwt_token
            token = create_jwt_token(test_user.id, test_user.email, test_user.role)

            response = client.get(
                '/api/encryption/keys',
                headers={'Authorization': f'Bearer {token}'}
            )

            assert response.status_code == 200
            keys = response.get_json()
            assert len(keys) == 2
            assert keys[0]['name'] == 'Key 2'  # Most recent first
            assert keys[1]['name'] == 'Key 1'

    def test_revoke_api_key(self, client, app, test_user):
        """Test revoking an API key"""
        with app.app_context():
            key = APIKey(
                user_id=test_user.id,
                name='To Revoke',
                prefix='pk_zzz999',
                encrypted_key=encryption_service.encrypt_field('secret'),
                expires_at=datetime.utcnow() + timedelta(days=30)
            )
            db.session.add(key)
            db.session.commit()
            key_id = key.id

            from backend.auth import create_jwt_token
            token = create_jwt_token(test_user.id, test_user.email, test_user.role)

            response = client.delete(
                f'/api/encryption/keys/{key_id}',
                json={'reason': 'Key compromised'},
                headers={'Authorization': f'Bearer {token}'}
            )

            assert response.status_code == 200
            data = response.get_json()
            assert data['id'] == key_id
            assert 'revoked_at' in data

            # Verify key is revoked in DB
            revoked_key = APIKey.query.get(key_id)
            assert revoked_key.is_active is False
            assert revoked_key.revocation_reason == 'Key compromised'

    def test_api_key_expiration(self, app, test_user):
        """Test that expired keys are detected"""
        with app.app_context():
            expired_key = APIKey(
                user_id=test_user.id,
                name='Expired',
                prefix='pk_exp999',
                encrypted_key=encryption_service.encrypt_field('secret'),
                expires_at=datetime.utcnow() - timedelta(hours=1)  # Expired
            )
            db.session.add(expired_key)
            db.session.commit()

            assert expired_key.is_expired()
            assert not expired_key.is_valid()

    def test_api_key_valid_check(self, app, test_user):
        """Test API key validity check"""
        with app.app_context():
            valid_key = APIKey(
                user_id=test_user.id,
                name='Valid',
                prefix='pk_valid123',
                encrypted_key=encryption_service.encrypt_field('secret'),
                expires_at=datetime.utcnow() + timedelta(days=30),
                is_active=True
            )
            db.session.add(valid_key)
            db.session.commit()

            assert not valid_key.is_expired()
            assert valid_key.is_valid()

            # Deactivate
            valid_key.is_active = False
            db.session.commit()
            assert not valid_key.is_valid()


# ============ AUDIT LOG TESTS ============

class TestAuditLogging:
    """Test audit log functionality"""

    def test_create_audit_log(self, app, test_user):
        """Test creating an audit log entry"""
        with app.app_context():
            log = AuditLog(
                user_id=test_user.id,
                action='api_key_created',
                resource_type='api_key',
                resource_id=1,
                ip_address='192.168.1.1',
                status='success'
            )
            db.session.add(log)
            db.session.commit()

            stored_log = AuditLog.query.first()
            assert stored_log.action == 'api_key_created'
            assert stored_log.resource_type == 'api_key'
            assert stored_log.status == 'success'

    def test_audit_log_timestamp(self, app, test_user):
        """Test that audit log has timestamp"""
        with app.app_context():
            before = datetime.utcnow()
            log = AuditLog(
                user_id=test_user.id,
                action='test_action',
                resource_type='test',
                status='success'
            )
            db.session.add(log)
            db.session.commit()
            after = datetime.utcnow()

            assert before <= log.timestamp <= after


# ============ KEY ROTATION TESTS ============

class TestKeyRotation:
    """Test encryption key rotation"""

    def test_create_rotation_record(self, app, test_user):
        """Test creating a key rotation record"""
        with app.app_context():
            rotation = EncryptionKeyRotation(
                old_key_version='v1',
                new_key_version='v2',
                initiated_by_user_id=test_user.id,
                rotation_status='pending',
                total_records=100
            )
            db.session.add(rotation)
            db.session.commit()

            stored = EncryptionKeyRotation.query.first()
            assert stored.rotation_status == 'pending'
            assert stored.total_records == 100
            assert stored.rotated_records == 0

    def test_rotation_progress_percent(self, app, test_user):
        """Test rotation progress calculation"""
        with app.app_context():
            rotation = EncryptionKeyRotation(
                old_key_version='v1',
                new_key_version='v2',
                initiated_by_user_id=test_user.id,
                rotation_status='in_progress',
                total_records=100,
                rotated_records=75
            )
            db.session.add(rotation)
            db.session.commit()

            assert rotation.to_dict()['progress_percent'] == 75

    def test_rotation_completion_check(self, app, test_user):
        """Test rotation completion check"""
        with app.app_context():
            # Complete rotation
            complete = EncryptionKeyRotation(
                old_key_version='v1',
                new_key_version='v2',
                initiated_by_user_id=test_user.id,
                rotation_status='completed',
                total_records=100,
                rotated_records=100,
                failed_records=0
            )
            assert complete.is_complete()

            # Failed rotation
            failed = EncryptionKeyRotation(
                old_key_version='v1',
                new_key_version='v2',
                initiated_by_user_id=test_user.id,
                rotation_status='completed',
                total_records=100,
                rotated_records=95,
                failed_records=5
            )
            assert not failed.is_complete()


# ============ ENCRYPTED TYPE DECORATOR TESTS ============

class TestEncryptedStringDecorator:
    """Test EncryptedString SQLAlchemy type decorator"""

    def test_encrypted_field_storage(self, app, test_user):
        """Test that fields are encrypted in database"""
        with app.app_context():
            # Create an API key with encrypted field
            original_key = "my_secret_key_123"
            encrypted = encryption_service.encrypt_field(original_key)

            api_key = APIKey(
                user_id=test_user.id,
                name='Test',
                prefix='pk_test123',
                encrypted_key=encrypted,
                expires_at=datetime.utcnow() + timedelta(days=30)
            )
            db.session.add(api_key)
            db.session.commit()

            # Retrieve and verify it's still encrypted in DB
            raw_query = db.session.execute(
                f"SELECT encrypted_key FROM api_keys WHERE id = {api_key.id}"
            )
            result = raw_query.fetchone()
            db_value = result[0] if result else None

            # The stored value should be encrypted (not plaintext)
            assert db_value != original_key
            assert db_value.startswith('gAAAAAA')  # Fernet token prefix


# ============ INTEGRATION TESTS ============

class TestEncryptionIntegration:
    """End-to-end encryption workflow tests"""

    def test_full_api_key_lifecycle(self, client, app, test_user):
        """Test complete API key lifecycle: create -> list -> use -> revoke"""
        with app.app_context():
            from backend.auth import create_jwt_token
            token = create_jwt_token(test_user.id, test_user.email, test_user.role)

            # Create
            create_resp = client.post(
                '/api/encryption/keys',
                json={'name': 'Lifecycle Test', 'expires_in_days': 30},
                headers={'Authorization': f'Bearer {token}'}
            )
            assert create_resp.status_code == 201
            created_key = create_resp.get_json()
            key_id = created_key['id']

            # List
            list_resp = client.get(
                '/api/encryption/keys',
                headers={'Authorization': f'Bearer {token}'}
            )
            assert list_resp.status_code == 200
            keys = list_resp.get_json()
            assert len(keys) >= 1

            # Revoke
            revoke_resp = client.delete(
                f'/api/encryption/keys/{key_id}',
                json={'reason': 'Testing'},
                headers={'Authorization': f'Bearer {token}'}
            )
            assert revoke_resp.status_code == 200

            # Verify revoked
            list_resp2 = client.get(
                '/api/encryption/keys',
                headers={'Authorization': f'Bearer {token}'}
            )
            active_keys = [k for k in list_resp2.get_json() if k['is_active']]
            assert len(active_keys) == 0
