#!/usr/bin/env python3
"""
Encryption Key Rotation Script

Safely re-encrypts all encrypted fields with a new master key.

Usage:
    python rotate_encryption_key.py <old_key> <new_key> [--dry-run]

Example:
    python rotate_encryption_key.py "old_fernet_key" "new_fernet_key"
    python rotate_encryption_key.py "old_key" "new_key" --dry-run
"""
import sys
import os
import logging
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from cryptography.fernet import Fernet, InvalidToken
from backend.app import create_app, db
from backend.models import EncryptionKeyRotation, AuditLog, User
from backend.encryption_service import EncryptionService

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class KeyRotationManager:
    """Handles encryption key rotation safely"""

    def __init__(self, old_key: str, new_key: str, dry_run: bool = False):
        """
        Initialize key rotation manager.

        Args:
            old_key: Old Fernet encryption key
            new_key: New Fernet encryption key
            dry_run: If True, only simulate rotation without writing to DB
        """
        self.dry_run = dry_run
        self.old_cipher = Fernet(old_key.encode() if isinstance(old_key, str) else old_key)
        self.new_cipher = Fernet(new_key.encode() if isinstance(new_key, str) else new_key)

        self.rotation_id = None
        self.total_records = 0
        self.rotated_records = 0
        self.failed_records = 0
        self.errors = []

    def start_rotation(self, app, user_id: int = None):
        """Start key rotation process"""
        with app.app_context():
            rotation = EncryptionKeyRotation(
                old_key_version='v1',
                new_key_version='v2',
                initiated_by_user_id=user_id,
                rotation_status='in_progress'
            )
            if not self.dry_run:
                db.session.add(rotation)
                db.session.commit()
                self.rotation_id = rotation.id
                logger.info(f"Started key rotation (ID: {rotation.id})")
            else:
                logger.info("DRY RUN: Key rotation started (no DB write)")

    def rotate_field(self, encrypted_value: str) -> str:
        """
        Decrypt with old key and encrypt with new key.

        Args:
            encrypted_value: Value encrypted with old key

        Returns:
            Value encrypted with new key

        Raises:
            ValueError: If decryption fails
        """
        try:
            if not encrypted_value:
                return None

            # Decrypt with old key
            if isinstance(encrypted_value, str):
                encrypted_value = encrypted_value.encode()
            decrypted = self.old_cipher.decrypt(encrypted_value)

            # Encrypt with new key
            re_encrypted = self.new_cipher.encrypt(decrypted).decode()

            self.rotated_records += 1
            return re_encrypted

        except InvalidToken as e:
            error_msg = f"Invalid token - may already be encrypted with new key"
            logger.warning(f"Failed to rotate field: {error_msg}")
            self.failed_records += 1
            self.errors.append(error_msg)
            raise ValueError(error_msg)
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Failed to rotate field: {error_msg}")
            self.failed_records += 1
            self.errors.append(error_msg)
            raise ValueError(f"Key rotation failed for field: {error_msg}")

    def complete_rotation(self, app, success: bool = True):
        """Complete the rotation process"""
        with app.app_context():
            if not self.dry_run and self.rotation_id:
                rotation = EncryptionKeyRotation.query.get(self.rotation_id)
                if rotation:
                    rotation.rotation_status = 'completed' if success else 'failed'
                    rotation.total_records = self.total_records
                    rotation.rotated_records = self.rotated_records
                    rotation.failed_records = self.failed_records
                    if self.errors:
                        rotation.error_details = '\n'.join(self.errors)
                    db.session.commit()
                    logger.info(f"Completed key rotation: {rotation.rotation_status}")
            else:
                logger.info("DRY RUN: Key rotation completed (no DB write)")

    def log_audit(self, app, user_id: int, details: str):
        """Log rotation action to audit log"""
        with app.app_context():
            if not self.dry_run:
                audit = AuditLog(
                    user_id=user_id,
                    action='encryption_key_rotated',
                    resource_type='encryption',
                    status='success',
                    details=details
                )
                db.session.add(audit)
                db.session.commit()


def rotate_api_keys(app, manager: KeyRotationManager):
    """Rotate API key encryption"""
    from backend.models import APIKey

    with app.app_context():
        api_keys = APIKey.query.filter_by(is_active=True).all()
        manager.total_records += len(api_keys)

        logger.info(f"Rotating {len(api_keys)} API keys...")

        for api_key in api_keys:
            try:
                new_encrypted = manager.rotate_field(api_key.encrypted_key)
                if not manager.dry_run:
                    api_key.encrypted_key = new_encrypted
                    db.session.add(api_key)
            except Exception as e:
                logger.error(f"Failed to rotate API key {api_key.id}: {e}")

        if not manager.dry_run:
            db.session.commit()
            logger.info(f"Successfully rotated {manager.rotated_records} API keys")
        else:
            logger.info(f"DRY RUN: Would rotate {len(api_keys)} API keys")


def main():
    """Main rotation process"""
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    old_key = sys.argv[1]
    new_key = sys.argv[2]
    dry_run = '--dry-run' in sys.argv

    logger.info(f"Key Rotation Service Started (dry_run={dry_run})")

    # Validate keys
    try:
        Fernet(old_key.encode() if isinstance(old_key, str) else old_key)
        Fernet(new_key.encode() if isinstance(new_key, str) else new_key)
        logger.info("Keys validated successfully")
    except Exception as e:
        logger.error(f"Invalid Fernet key: {e}")
        sys.exit(1)

    # Initialize app
    app = create_app()
    manager = KeyRotationManager(old_key, new_key, dry_run=dry_run)

    try:
        # Start rotation
        manager.start_rotation(app, user_id=None)

        # Rotate all encrypted fields
        rotate_api_keys(app, manager)

        # Complete rotation
        manager.complete_rotation(app, success=manager.failed_records == 0)

        # Log audit
        manager.log_audit(app, None,
            f"Key rotation completed: {manager.rotated_records} rotated, {manager.failed_records} failed")

        # Summary
        logger.info("=" * 60)
        logger.info("KEY ROTATION SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total records processed: {manager.total_records}")
        logger.info(f"Successfully rotated: {manager.rotated_records}")
        logger.info(f"Failed: {manager.failed_records}")
        logger.info(f"Status: {'COMPLETED' if manager.failed_records == 0 else 'FAILED'}")
        logger.info("=" * 60)

        sys.exit(0 if manager.failed_records == 0 else 1)

    except Exception as e:
        logger.error(f"Key rotation failed: {e}", exc_info=True)
        manager.complete_rotation(app, success=False)
        sys.exit(1)


if __name__ == '__main__':
    main()
