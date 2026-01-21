"""
License signing and verification.
Handles RSA signature operations for license files.
"""

import base64
import sys
from pathlib import Path
from typing import Optional

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.backends import default_backend

from .license_model import License
from ..logger import get_logger

logger = get_logger("licensing.signer")


def generate_key_pair() -> tuple[rsa.RSAPrivateKey, rsa.RSAPublicKey]:
    """
    Generate a new RSA key pair.
    
    Returns:
        Tuple of (private_key, public_key)
    """
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    public_key = private_key.public_key()
    return private_key, public_key


def load_private_key(key_path: Path) -> Optional[rsa.RSAPrivateKey]:
    """
    Load private key from PEM file.
    
    Args:
        key_path: Path to private key file
        
    Returns:
        RSAPrivateKey object or None if error
    """
    try:
        with open(key_path, 'rb') as f:
            private_key = serialization.load_pem_private_key(
                f.read(),
                password=None,
                backend=default_backend()
            )
        return private_key
    except Exception as e:
        logger.error(f"Error loading private key: {e}")
        return None


def load_public_key(key_path: Path) -> Optional[rsa.RSAPublicKey]:
    """
    Load public key from PEM file.
    
    Args:
        key_path: Path to public key file
        
    Returns:
        RSAPublicKey object or None if error
    """
    try:
        with open(key_path, 'rb') as f:
            public_key = serialization.load_pem_public_key(
                f.read(),
                backend=default_backend()
            )
        return public_key
    except Exception as e:
        logger.error(f"Error loading public key: {e}")
        return None


def get_embedded_public_key() -> Optional[rsa.RSAPublicKey]:
    """
    Get the embedded public key for license verification.
    This key should be embedded in the application.
    
    Returns:
        RSAPublicKey object or None if not found
    """
    # Check multiple possible locations
    
    # 1. PyInstaller bundle location (when packaged)
    if hasattr(sys, '_MEIPASS'):
        # Running from PyInstaller bundle
        bundle_dir = Path(sys._MEIPASS)
        public_key_path = bundle_dir / 'pdf_merger' / 'licensing' / 'public_key.pem'
        if public_key_path.exists():
            return load_public_key(public_key_path)
    
    # 2. App directory (for packaged app - macOS .app bundle)
    app_dir = Path(__file__).parent.parent.parent
    public_key_path = app_dir / 'public_key.pem'
    if public_key_path.exists():
        return load_public_key(public_key_path)
    
    # 3. Licensing directory (for development and PyInstaller data)
    licensing_dir = Path(__file__).parent
    public_key_path = licensing_dir / 'public_key.pem'
    if public_key_path.exists():
        return load_public_key(public_key_path)
    
    # 4. Try relative to main.py (for development)
    try:
        main_dir = Path(__file__).parent.parent.parent
        public_key_path = main_dir / 'pdf_merger' / 'licensing' / 'public_key.pem'
        if public_key_path.exists():
            return load_public_key(public_key_path)
    except Exception:
        pass
    
    logger.warning("Embedded public key not found in any expected location")
    return None


def sign_license(license: License, private_key: rsa.RSAPrivateKey) -> bool:
    """
    Sign a license with a private key.
    
    Args:
        license: License object to sign
        private_key: Private key for signing
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Create JSON string without signature
        license_json = license.to_json_string()
        
        # Sign the license data
        signature = private_key.sign(
            license_json.encode('utf-8'),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        
        # Encode signature as base64
        license.signature = base64.b64encode(signature).decode('utf-8')
        
        logger.info("License signed successfully")
        return True
    except Exception as e:
        logger.error(f"Error signing license: {e}")
        return False


def verify_license_signature(license: License, public_key: rsa.RSAPublicKey) -> bool:
    """
    Verify the signature of a license.
    
    Args:
        license: License object to verify
        public_key: Public key for verification
        
    Returns:
        True if signature is valid, False otherwise
    """
    if not license.signature:
        logger.warning("License has no signature")
        return False
    
    try:
        # Get license JSON without signature
        license_json = license.to_json_string()
        
        # Decode signature from base64
        signature_bytes = base64.b64decode(license.signature)
        
        # Verify signature
        public_key.verify(
            signature_bytes,
            license_json.encode('utf-8'),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        
        logger.info("License signature verified successfully")
        return True
    except Exception as e:
        logger.warning(f"License signature verification failed: {e}")
        return False


def save_private_key(private_key: rsa.RSAPrivateKey, key_path: Path) -> bool:
    """
    Save private key to PEM file.
    
    Args:
        private_key: Private key to save
        key_path: Path to save the key
        
    Returns:
        True if successful, False otherwise
    """
    try:
        key_path.parent.mkdir(parents=True, exist_ok=True)
        pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        with open(key_path, 'wb') as f:
            f.write(pem)
        logger.info(f"Private key saved to {key_path}")
        return True
    except Exception as e:
        logger.error(f"Error saving private key: {e}")
        return False


def save_public_key(public_key: rsa.RSAPublicKey, key_path: Path) -> bool:
    """
    Save public key to PEM file.
    
    Args:
        public_key: Public key to save
        key_path: Path to save the key
        
    Returns:
        True if successful, False otherwise
    """
    try:
        key_path.parent.mkdir(parents=True, exist_ok=True)
        pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        with open(key_path, 'wb') as f:
            f.write(pem)
        logger.info(f"Public key saved to {key_path}")
        return True
    except Exception as e:
        logger.error(f"Error saving public key: {e}")
        return False
