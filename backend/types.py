"""
Custom SQLAlchemy column types for field-level encryption
"""
from sqlalchemy.types import TypeDecorator, String, TEXT
from sqlalchemy import event
import logging

from .encryption_service import encryption_service

logger = logging.getLogger(__name__)


class EncryptedString(TypeDecorator):
    """
    SQLAlchemy TypeDecorator for encrypted VARCHAR fields.

    Automatically encrypts on write and decrypts on read.
    Works with both bind parameters and result processing.

    Example:
        phone_number = db.Column(EncryptedString(20))
        ssn = db.Column(EncryptedString(11))
    """

    impl = String
    cache_ok = True

    def process_bind_param(self, value, dialect):
        """Encrypt data before storing in database"""
        if value is None:
            return None

        try:
            return encryption_service.encrypt_field(value)
        except Exception as e:
            logger.error(f"EncryptedString: Failed to encrypt on bind: {e}")
            # In production, this should raise. For dev, we might log and continue.
            raise

    def process_result_value(self, value, dialect):
        """Decrypt data when retrieving from database"""
        if value is None:
            return None

        try:
            return encryption_service.decrypt_field(value)
        except Exception as e:
            logger.error(f"EncryptedString: Failed to decrypt on result: {e}")
            # Return None or raise based on your error handling strategy
            raise


class EncryptedText(TypeDecorator):
    """
    SQLAlchemy TypeDecorator for encrypted TEXT fields.

    Similar to EncryptedString but for larger text content.

    Example:
        biography = db.Column(EncryptedText())
        notes = db.Column(EncryptedText())
    """

    impl = TEXT
    cache_ok = True

    def process_bind_param(self, value, dialect):
        """Encrypt data before storing in database"""
        if value is None:
            return None

        try:
            return encryption_service.encrypt_field(value)
        except Exception as e:
            logger.error(f"EncryptedText: Failed to encrypt on bind: {e}")
            raise

    def process_result_value(self, value, dialect):
        """Decrypt data when retrieving from database"""
        if value is None:
            return None

        try:
            return encryption_service.decrypt_field(value)
        except Exception as e:
            logger.error(f"EncryptedText: Failed to decrypt on result: {e}")
            raise
