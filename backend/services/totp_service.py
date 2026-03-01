"""2FA/TOTP Service — Setup, Verification, and Backup Code Management"""
import pyotp
import qrcode
import json
import secrets
from io import BytesIO
import base64
from datetime import datetime
from cryptography.fernet import Fernet
import os


class TOTPService:
    """Manage Two-Factor Authentication (TOTP) via authenticator apps."""

    def __init__(self):
        # Get encryption key from environment or use a default (NOT for production!)
        encryption_key = os.getenv('TOTP_ENCRYPTION_KEY')
        if not encryption_key:
            # Generate and store a key for this session
            encryption_key = Fernet.generate_key().decode()
        self.cipher = Fernet(encryption_key.encode() if isinstance(encryption_key, str) else encryption_key)

    @staticmethod
    def generate_secret() -> str:
        """Generate a random base32-encoded secret for TOTP.

        Returns:
            str: Base32 encoded secret suitable for pyotp
        """
        return pyotp.random_base32()

    @staticmethod
    def generate_qr_code(secret: str, email: str, issuer: str = "SoftFactory") -> str:
        """Generate QR code for TOTP secret.

        Args:
            secret: Base32 encoded TOTP secret
            email: User email (displayed as account identifier)
            issuer: Name of the service (displayed on authenticator apps)

        Returns:
            str: Base64 encoded PNG image of QR code
        """
        totp = pyotp.TOTP(secret)
        uri = totp.provisioning_uri(name=email, issuer_name=issuer)

        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(uri)
        qr.make(fit=True)

        # Convert to PIL Image
        img = qr.make_image(fill_color="black", back_color="white")

        # Convert to base64
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        img_base64 = base64.b64encode(buffer.getvalue()).decode()

        return f"data:image/png;base64,{img_base64}"

    def generate_backup_codes(self, count: int = 10) -> list[str]:
        """Generate backup codes for account recovery.

        Args:
            count: Number of backup codes to generate (default: 10)

        Returns:
            list[str]: List of backup codes (unencrypted for display)
        """
        codes = []
        for _ in range(count):
            # Generate 8-character alphanumeric codes
            code = secrets.token_hex(4).upper()  # 8 hex chars
            codes.append(code)
        return codes

    def encrypt_backup_codes(self, codes: list[str]) -> str:
        """Encrypt backup codes for storage.

        Args:
            codes: List of backup codes

        Returns:
            str: Encrypted JSON string
        """
        json_str = json.dumps(codes)
        encrypted = self.cipher.encrypt(json_str.encode())
        return encrypted.decode()

    def decrypt_backup_codes(self, encrypted_codes: str) -> list[str]:
        """Decrypt backup codes from storage.

        Args:
            encrypted_codes: Encrypted JSON string

        Returns:
            list[str]: List of backup codes
        """
        try:
            decrypted = self.cipher.decrypt(encrypted_codes.encode())
            return json.loads(decrypted.decode())
        except Exception:
            return []

    @staticmethod
    def verify_totp(secret: str, token: str, window: int = 1) -> bool:
        """Verify a TOTP token against a secret.

        Args:
            secret: Base32 encoded TOTP secret
            token: 6-digit TOTP code entered by user
            window: Time window for verification (±window*30 seconds)

        Returns:
            bool: True if token is valid
        """
        try:
            totp = pyotp.TOTP(secret)
            # Allow time window drift for clock skew
            return totp.verify(token, valid_window=window)
        except Exception:
            return False

    def verify_backup_code(self, encrypted_codes: str, used_codes_json: str, code: str) -> tuple[bool, str]:
        """Verify and consume a backup code.

        Args:
            encrypted_codes: Encrypted backup codes from DB
            used_codes_json: JSON string of used code indexes
            code: Backup code entered by user

        Returns:
            tuple[bool, str]: (is_valid, updated_used_codes_json)
        """
        try:
            backup_codes = self.decrypt_backup_codes(encrypted_codes)
            used_indexes = json.loads(used_codes_json)

            for idx, backup_code in enumerate(backup_codes):
                if idx not in used_indexes and backup_code == code.upper():
                    # Mark as used
                    used_indexes.append(idx)
                    updated_json = json.dumps(used_indexes)
                    return True, updated_json

            return False, used_codes_json
        except Exception:
            return False, used_codes_json

    @staticmethod
    def get_remaining_backup_codes(encrypted_codes: str, used_codes_json: str) -> int:
        """Get number of remaining backup codes.

        Args:
            encrypted_codes: Encrypted backup codes
            used_codes_json: JSON string of used code indexes

        Returns:
            int: Number of unused backup codes
        """
        try:
            service = TOTPService()
            backup_codes = service.decrypt_backup_codes(encrypted_codes)
            used_indexes = json.loads(used_codes_json)
            return len(backup_codes) - len(used_indexes)
        except Exception:
            return 0


# Singleton instance
_totp_service = None

def get_totp_service() -> TOTPService:
    """Get or create TOTP service singleton."""
    global _totp_service
    if _totp_service is None:
        _totp_service = TOTPService()
    return _totp_service
