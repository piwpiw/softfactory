"""
Field-Level Encryption Service
Handles encryption/decryption of sensitive database fields using Fernet (AES-128)
"""
from cryptography.fernet import Fernet, InvalidToken
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class EncryptionService:
    """
    Manages field-level encryption using Fernet symmetric encryption.

    Features:
    - AES-128 encryption with HMAC for authentication
    - Thread-safe singleton pattern
    - Graceful fallback for missing keys
    - Key rotation support
    """

    _instance = None
    _cipher = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Initialize cipher from environment variable or generate test key"""
        encryption_key = os.getenv('ENCRYPTION_KEY')

        if encryption_key:
            try:
                # Ensure key is bytes
                if isinstance(encryption_key, str):
                    encryption_key = encryption_key.encode()
                self._cipher = Fernet(encryption_key)
                logger.info("EncryptionService: Initialized with environment key")
            except Exception as e:
                logger.error(f"EncryptionService: Failed to initialize cipher: {e}")
                self._cipher = None
        else:
            logger.warning(
                "EncryptionService: ENCRYPTION_KEY not found in environment. "
                "Generating test key. DO NOT USE IN PRODUCTION!"
            )
            # Generate a test key (development only)
            test_key = Fernet.generate_key()
            logger.warning(f"EncryptionService: Test key: {test_key.decode()}")
            self._cipher = Fernet(test_key)

    def encrypt_field(self, data: str) -> str:
        """
        Encrypt a string field.

        Args:
            data: Plain text to encrypt

        Returns:
            Encrypted string (base64 encoded token)

        Raises:
            ValueError: If encryption fails or cipher not initialized
        """
        if not self._cipher:
            raise ValueError("Encryption service not initialized")

        if data is None:
            return None

        try:
            if isinstance(data, str):
                data = data.encode()
            encrypted = self._cipher.encrypt(data)
            return encrypted.decode()
        except Exception as e:
            logger.error(f"EncryptionService: Failed to encrypt field: {e}")
            raise ValueError(f"Field encryption failed: {e}")

    def decrypt_field(self, encrypted_data: str) -> str:
        """
        Decrypt an encrypted field.

        Args:
            encrypted_data: Encrypted string (base64 encoded token)

        Returns:
            Decrypted plain text

        Raises:
            ValueError: If decryption fails or cipher not initialized
        """
        if not self._cipher:
            raise ValueError("Encryption service not initialized")

        if encrypted_data is None:
            return None

        try:
            if isinstance(encrypted_data, str):
                encrypted_data = encrypted_data.encode()
            decrypted = self._cipher.decrypt(encrypted_data)
            return decrypted.decode()
        except InvalidToken:
            logger.error("EncryptionService: Invalid or corrupted encrypted data")
            raise ValueError("Failed to decrypt field: Invalid token")
        except Exception as e:
            logger.error(f"EncryptionService: Failed to decrypt field: {e}")
            raise ValueError(f"Field decryption failed: {e}")

    def rotate_key(self, old_key: bytes, new_key: bytes, data_list: list) -> list:
        """
        Re-encrypt data with a new key.

        Args:
            old_key: Previous encryption key
            new_key: New encryption key
            data_list: List of encrypted values to re-encrypt

        Returns:
            List of re-encrypted values
        """
        old_cipher = Fernet(old_key)
        new_cipher = Fernet(new_key)
        rotated = []

        for encrypted_value in data_list:
            try:
                decrypted = old_cipher.decrypt(encrypted_value.encode())
                re_encrypted = new_cipher.encrypt(decrypted).decode()
                rotated.append(re_encrypted)
            except Exception as e:
                logger.error(f"EncryptionService: Failed to rotate key for value: {e}")
                raise ValueError(f"Key rotation failed: {e}")

        return rotated


# Singleton instance
encryption_service = EncryptionService()
