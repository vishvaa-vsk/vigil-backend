from cryptography.fernet import Fernet
from app.core.config import settings
import base64

class CredentialEncryption:
    """Handle encryption/decryption of sensitive credentials"""

    def __init__(self):
        """Initialize with encryption key from environment"""
        self.key = self._get_or_create_key()
        self.fernet = Fernet(self.key)

    def _get_or_create_key(self) -> bytes:
        """
        Get encryption key from environment or create one
        In production, store this securely (e.g., AWS KMS, HashiCorp Vault)
        """
        key_str = settings.encryption_key

        if not key_str:
            key = Fernet.generate_key()
            print(f"⚠️ Generated new encryption key: {key.decode()}")
            print("⚠️ Store this in ENCRYPTION_KEY environment variable!")
            return key
        
        return key_str.encode() if isinstance(key_str, str) else key_str

    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt plaintext string
        
        Args:
            plaintext: String to encrypt (e.g., GitHub token, Sentry DSN)
        
        Returns:
            Encrypted string (base64 encoded for storage)
        """
        if not plaintext:
            return ""
        try:
            encrypted = self.fernet.encrypt(plaintext.encode())
            return base64.b64encode(encrypted).decode()
        except Exception as e:
            print(f"❌ Encryption error: {str(e)}")
            raise ValueError("Encryption failed")
    
    def decrypt(self, encrypted_b64: str) -> str:
        """
        Decrypt encrypted string
        
        Args:
            encrypted_b64: Encrypted string (base64 encoded)
        
        Returns:
            Decrypted plaintext string
        """
        if not encrypted_b64:
            return ""
        try:
            encrypted = base64.b64decode(encrypted_b64.encode())
            decrypted = self.fernet.decrypt(encrypted)
            return decrypted.decode()
        except Exception as e:
            print(f"❌ Decryption error: {str(e)}")
            raise ValueError("Decryption failed")

credential_encryption = CredentialEncryption()