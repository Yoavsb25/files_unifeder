"""
Unit tests for licensing modules.
"""

import json
import pytest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

# Try to import cryptography, skip tests if not available
try:
    from cryptography.hazmat.primitives.asymmetric import rsa
    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False
    rsa = None

from pdf_merger.licensing.license_model import License
from pdf_merger.licensing.license_signer import (
    generate_key_pair,
    load_private_key,
    load_public_key,
    sign_license,
    verify_license_signature,
    save_private_key,
    save_public_key,
    get_embedded_public_key
)
from pdf_merger.licensing.license_manager import (
    LicenseManager,
    LicenseStatus
)

# Skip all tests if cryptography is not available
pytestmark = pytest.mark.skipif(
    not CRYPTOGRAPHY_AVAILABLE,
    reason="cryptography module not available"
)


class TestLicense:
    """Test cases for License dataclass."""
    
    def test_license_creation(self):
        """Test creating a License instance."""
        license = License(
            company="Test Company",
            expires="2027-12-31",
            allowed_machines=5,
            version="1.0.0",
            signature="test_signature"
        )
        
        assert license.company == "Test Company"
        assert license.expires == "2027-12-31"
        assert license.allowed_machines == 5
        assert license.version == "1.0.0"
        assert license.signature == "test_signature"
    
    def test_license_to_dict(self):
        """Test converting license to dictionary without signature."""
        license = License(
            company="Test Company",
            expires="2027-12-31",
            allowed_machines=5,
            version="1.0.0",
            signature="test_signature"
        )
        
        result = license.to_dict()
        
        assert result['company'] == "Test Company"
        assert result['expires'] == "2027-12-31"
        assert result['allowed_machines'] == 5
        assert result['version'] == "1.0.0"
        assert 'signature' not in result
    
    def test_license_to_dict_with_signature(self):
        """Test converting license to dictionary with signature."""
        license = License(
            company="Test Company",
            expires="2027-12-31",
            allowed_machines=5,
            version="1.0.0",
            signature="test_signature"
        )
        
        result = license.to_dict_with_signature()
        
        assert result['signature'] == "test_signature"
    
    def test_license_from_dict(self):
        """Test creating license from dictionary."""
        data = {
            'company': 'Test Company',
            'expires': '2027-12-31',
            'allowed_machines': 5,
            'version': '1.0.0',
            'signature': 'test_signature'
        }
        
        license = License.from_dict(data)
        
        assert license.company == "Test Company"
        assert license.expires == "2027-12-31"
        assert license.allowed_machines == 5
        assert license.version == "1.0.0"
        assert license.signature == "test_signature"
    
    def test_license_from_dict_defaults(self):
        """Test creating license from dictionary with missing fields."""
        data = {
            'company': 'Test Company',
            'expires': '2027-12-31'
        }
        
        license = License.from_dict(data)
        
        assert license.company == "Test Company"
        assert license.allowed_machines == 0
        assert license.version == "1.0.0"
        assert license.signature is None
    
    def test_license_is_expired_future(self):
        """Test checking if license is expired (future date)."""
        future_date = (datetime.now() + timedelta(days=365)).strftime('%Y-%m-%d')
        license = License(
            company="Test",
            expires=future_date,
            allowed_machines=1,
            version="1.0.0"
        )
        
        assert license.is_expired() is False
    
    def test_license_is_expired_past(self):
        """Test checking if license is expired (past date)."""
        past_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        license = License(
            company="Test",
            expires=past_date,
            allowed_machines=1,
            version="1.0.0"
        )
        
        assert license.is_expired() is True
    
    def test_license_is_expired_invalid_format(self):
        """Test checking expiration with invalid date format."""
        license = License(
            company="Test",
            expires="invalid-date",
            allowed_machines=1,
            version="1.0.0"
        )
        
        assert license.is_expired() is True
    
    def test_license_to_json_string(self):
        """Test converting license to JSON string."""
        license = License(
            company="Test Company",
            expires="2027-12-31",
            allowed_machines=5,
            version="1.0.0"
        )
        
        json_str = license.to_json_string()
        
        assert isinstance(json_str, str)
        data = json.loads(json_str)
        assert data['company'] == "Test Company"
        assert 'signature' not in data
    
    def test_license_load_from_file(self, tmp_path):
        """Test loading license from file."""
        license_file = tmp_path / "license.json"
        license_data = {
            'company': 'Test Company',
            'expires': '2027-12-31',
            'allowed_machines': 5,
            'version': '1.0.0',
            'signature': 'test_signature'
        }
        license_file.write_text(json.dumps(license_data))
        
        license = License.load_from_file(license_file)
        
        assert license is not None
        assert license.company == "Test Company"
    
    def test_license_load_from_file_not_found(self, tmp_path):
        """Test loading license from non-existent file."""
        license_file = tmp_path / "nonexistent.json"
        
        license = License.load_from_file(license_file)
        
        assert license is None
    
    def test_license_load_from_file_invalid_json(self, tmp_path):
        """Test loading license from invalid JSON file."""
        license_file = tmp_path / "license.json"
        license_file.write_text("invalid json {")
        
        license = License.load_from_file(license_file)
        
        assert license is None
    
    def test_license_save_to_file(self, tmp_path):
        """Test saving license to file."""
        license_file = tmp_path / "license.json"
        license = License(
            company="Test Company",
            expires="2027-12-31",
            allowed_machines=5,
            version="1.0.0",
            signature="test_signature"
        )
        
        result = license.save_to_file(license_file)
        
        assert result is True
        assert license_file.exists()
        
        # Verify content
        loaded_data = json.loads(license_file.read_text())
        assert loaded_data['company'] == "Test Company"
        assert loaded_data['signature'] == "test_signature"
    
    def test_license_save_to_file_creates_directory(self, tmp_path):
        """Test saving license creates parent directory."""
        license_dir = tmp_path / "new_dir"
        license_file = license_dir / "license.json"
        license = License(
            company="Test",
            expires="2027-12-31",
            allowed_machines=1,
            version="1.0.0"
        )
        
        result = license.save_to_file(license_file)
        
        assert result is True
        assert license_dir.exists()
        assert license_file.exists()
    
    def test_license_save_to_file_error(self, tmp_path):
        """Test saving license when write fails."""
        license = License(
            company="Test",
            expires="2027-12-31",
            allowed_machines=1,
            version="1.0.0"
        )
        
        with patch('builtins.open', side_effect=IOError("Write error")):
            result = license.save_to_file(tmp_path / "license.json")
            
            assert result is False


class TestLicenseSigner:
    """Test cases for license signing functions."""
    
    def test_generate_key_pair(self):
        """Test generating RSA key pair."""
        private_key, public_key = generate_key_pair()
        
        assert isinstance(private_key, rsa.RSAPrivateKey)
        assert isinstance(public_key, rsa.RSAPublicKey)
    
    def test_save_and_load_private_key(self, tmp_path):
        """Test saving and loading private key."""
        private_key, public_key = generate_key_pair()
        key_path = tmp_path / "private_key.pem"
        
        # Save
        result = save_private_key(private_key, key_path)
        assert result is True
        assert key_path.exists()
        
        # Load
        loaded_key = load_private_key(key_path)
        assert loaded_key is not None
        assert isinstance(loaded_key, rsa.RSAPrivateKey)
    
    def test_save_and_load_public_key(self, tmp_path):
        """Test saving and loading public key."""
        private_key, public_key = generate_key_pair()
        key_path = tmp_path / "public_key.pem"
        
        # Save
        result = save_public_key(public_key, key_path)
        assert result is True
        assert key_path.exists()
        
        # Load
        loaded_key = load_public_key(key_path)
        assert loaded_key is not None
        assert isinstance(loaded_key, rsa.RSAPublicKey)
    
    def test_load_private_key_not_found(self, tmp_path):
        """Test loading non-existent private key."""
        key_path = tmp_path / "nonexistent.pem"
        
        result = load_private_key(key_path)
        
        assert result is None
    
    def test_load_public_key_not_found(self, tmp_path):
        """Test loading non-existent public key."""
        key_path = tmp_path / "nonexistent.pem"
        
        result = load_public_key(key_path)
        
        assert result is None
    
    def test_sign_and_verify_license(self):
        """Test signing and verifying a license."""
        private_key, public_key = generate_key_pair()
        license = License(
            company="Test Company",
            expires="2027-12-31",
            allowed_machines=5,
            version="1.0.0"
        )
        
        # Sign
        result = sign_license(license, private_key)
        assert result is True
        assert license.signature is not None
        
        # Verify
        verify_result = verify_license_signature(license, public_key)
        assert verify_result is True
    
    def test_verify_license_invalid_signature(self):
        """Test verifying license with invalid signature."""
        private_key, public_key = generate_key_pair()
        license = License(
            company="Test Company",
            expires="2027-12-31",
            allowed_machines=5,
            version="1.0.0",
            signature="invalid_signature"
        )
        
        result = verify_license_signature(license, public_key)
        
        assert result is False
    
    def test_verify_license_no_signature(self):
        """Test verifying license without signature."""
        private_key, public_key = generate_key_pair()
        license = License(
            company="Test Company",
            expires="2027-12-31",
            allowed_machines=5,
            version="1.0.0"
        )
        
        result = verify_license_signature(license, public_key)
        
        assert result is False
    
    def test_verify_license_wrong_key(self):
        """Test verifying license with wrong public key."""
        private_key1, public_key1 = generate_key_pair()
        private_key2, public_key2 = generate_key_pair()
        
        license = License(
            company="Test Company",
            expires="2027-12-31",
            allowed_machines=5,
            version="1.0.0"
        )
        
        # Sign with key1
        sign_license(license, private_key1)
        
        # Verify with key2 (should fail)
        result = verify_license_signature(license, public_key2)
        
        assert result is False
    
    @patch('pdf_merger.licensing.license_signer.sys')
    def test_get_embedded_public_key_pyinstaller(self, mock_sys, tmp_path):
        """Test getting embedded public key from PyInstaller bundle."""
        # Mock PyInstaller environment
        mock_sys._MEIPASS = str(tmp_path)
        public_key_file = tmp_path / "pdf_merger" / "licensing" / "public_key.pem"
        public_key_file.parent.mkdir(parents=True)
        
        private_key, public_key = generate_key_pair()
        save_public_key(public_key, public_key_file)
        
        result = get_embedded_public_key()
        
        assert result is not None
        assert isinstance(result, rsa.RSAPublicKey)
    
    def test_get_embedded_public_key_licensing_dir(self, tmp_path):
        """Test getting embedded public key from licensing directory."""
        licensing_dir = tmp_path / "pdf_merger" / "licensing"
        licensing_dir.mkdir(parents=True)
        public_key_file = licensing_dir / "public_key.pem"
        
        private_key, public_key = generate_key_pair()
        save_public_key(public_key, public_key_file)
        
        with patch('pdf_merger.licensing.license_signer.Path') as mock_path:
            mock_file_path = MagicMock()
            mock_file_path.parent = licensing_dir.parent
            mock_path.return_value = mock_file_path
            mock_path.side_effect = lambda *args: Path(*args)
            
            with patch('pdf_merger.licensing.license_signer.__file__', str(licensing_dir / 'license_signer.py')):
                # Mock sys._MEIPASS to not exist
                with patch('pdf_merger.licensing.license_signer.sys') as mock_sys:
                    if hasattr(mock_sys, '_MEIPASS'):
                        delattr(mock_sys, '_MEIPASS')
                    
                    result = get_embedded_public_key()
                    
                    # Should find it in licensing directory
                    assert result is not None
    
    def test_get_embedded_public_key_not_found(self, tmp_path):
        """Test getting embedded public key when not found."""
        # Create a directory structure without public key
        licensing_dir = tmp_path / "pdf_merger" / "licensing"
        licensing_dir.mkdir(parents=True)
        
        with patch('pdf_merger.licensing.license_signer.sys') as mock_sys:
            # Remove _MEIPASS if it exists
            if hasattr(mock_sys, '_MEIPASS'):
                delattr(mock_sys, '_MEIPASS')
            
            with patch('pdf_merger.licensing.license_signer.__file__', str(licensing_dir / 'license_signer.py')):
                result = get_embedded_public_key()
                
                # Should return None when no public key found
                assert result is None


class TestLicenseManager:
    """Test cases for LicenseManager."""
    
    def test_license_manager_initialization(self):
        """Test initializing LicenseManager."""
        manager = LicenseManager(app_version="1.0.0")
        
        assert manager.app_version == "1.0.0"
        assert manager._cached_license is None
        assert manager._cached_status is None
    
    def test_get_license_path_app_directory(self, tmp_path):
        """Test getting license path from app directory."""
        app_dir = tmp_path / "app"
        app_dir.mkdir()
        license_file = app_dir / "license.json"
        license_file.write_text("{}")
        
        manager = LicenseManager()
        
        # Mock __file__ to point to app_dir
        with patch('pdf_merger.licensing.license_manager.__file__', str(app_dir / 'license_manager.py')):
            result = manager.get_license_path()
            
            # Should return a path (either app directory or home fallback)
            assert 'license.json' in str(result) or result.name == 'license.json'
    
    def test_load_license_success(self, tmp_path):
        """Test successfully loading license."""
        license_file = tmp_path / "license.json"
        license_data = {
            'company': 'Test Company',
            'expires': (datetime.now() + timedelta(days=365)).strftime('%Y-%m-%d'),
            'allowed_machines': 5,
            'version': '1.0.0',
            'signature': 'test'
        }
        license_file.write_text(json.dumps(license_data))
        
        manager = LicenseManager()
        
        with patch.object(manager, 'get_license_path', return_value=license_file):
            result = manager.load_license()
            
            assert result is not None
            assert result.company == "Test Company"
    
    def test_load_license_not_found(self, tmp_path):
        """Test loading license when file doesn't exist."""
        license_file = tmp_path / "nonexistent.json"
        
        manager = LicenseManager()
        
        with patch.object(manager, 'get_license_path', return_value=license_file):
            result = manager.load_license()
            
            assert result is None
    
    def test_validate_license_valid(self):
        """Test validating a valid license."""
        future_date = (datetime.now() + timedelta(days=365)).strftime('%Y-%m-%d')
        license = License(
            company="Test Company",
            expires=future_date,
            allowed_machines=5,
            version="1.0.0"
        )
        
        private_key, public_key = generate_key_pair()
        sign_license(license, private_key)
        
        manager = LicenseManager(app_version="1.0.0")
        
        with patch('pdf_merger.licensing.license_manager.get_embedded_public_key', return_value=public_key):
            result = manager.validate_license(license)
            
            assert result == LicenseStatus.VALID
    
    def test_validate_license_expired(self):
        """Test validating an expired license."""
        past_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        license = License(
            company="Test Company",
            expires=past_date,
            allowed_machines=5,
            version="1.0.0"
        )
        
        private_key, public_key = generate_key_pair()
        sign_license(license, private_key)
        
        manager = LicenseManager(app_version="1.0.0")
        
        with patch('pdf_merger.licensing.license_manager.get_embedded_public_key', return_value=public_key):
            result = manager.validate_license(license)
            
            assert result == LicenseStatus.EXPIRED
    
    def test_validate_license_invalid_signature(self):
        """Test validating license with invalid signature."""
        future_date = (datetime.now() + timedelta(days=365)).strftime('%Y-%m-%d')
        license = License(
            company="Test Company",
            expires=future_date,
            allowed_machines=5,
            version="1.0.0",
            signature="invalid"
        )
        
        private_key, public_key = generate_key_pair()
        
        manager = LicenseManager(app_version="1.0.0")
        
        with patch('pdf_merger.licensing.license_manager.get_embedded_public_key', return_value=public_key):
            result = manager.validate_license(license)
            
            assert result == LicenseStatus.INVALID_SIGNATURE
    
    def test_validate_license_version_mismatch(self):
        """Test validating license with version mismatch."""
        future_date = (datetime.now() + timedelta(days=365)).strftime('%Y-%m-%d')
        license = License(
            company="Test Company",
            expires=future_date,
            allowed_machines=5,
            version="2.0.0"  # Different version
        )
        
        private_key, public_key = generate_key_pair()
        sign_license(license, private_key)
        
        manager = LicenseManager(app_version="1.0.0")
        
        with patch('pdf_merger.licensing.license_manager.get_embedded_public_key', return_value=public_key):
            result = manager.validate_license(license)
            
            assert result == LicenseStatus.VERSION_MISMATCH
    
    @patch.object(LicenseManager, 'load_license')
    def test_validate_license_not_found(self, mock_load_license):
        """Test validating when license is None."""
        manager = LicenseManager()
        mock_load_license.return_value = None
        
        result = manager.validate_license(None)
        
        assert result == LicenseStatus.NOT_FOUND
    
    def test_get_license_status(self):
        """Test getting license status with caching."""
        future_date = (datetime.now() + timedelta(days=365)).strftime('%Y-%m-%d')
        license = License(
            company="Test Company",
            expires=future_date,
            allowed_machines=5,
            version="1.0.0"
        )
        
        private_key, public_key = generate_key_pair()
        sign_license(license, private_key)
        
        manager = LicenseManager(app_version="1.0.0")
        
        with patch.object(manager, 'load_license', return_value=license):
            with patch('pdf_merger.licensing.license_manager.get_embedded_public_key', return_value=public_key):
                # First call
                result1 = manager.get_license_status()
                
                # Second call (should use cache)
                result2 = manager.get_license_status()
                
                assert result1 == LicenseStatus.VALID
                assert result2 == LicenseStatus.VALID
                # Should only load once
                assert manager.load_license.call_count == 1
    
    def test_get_license_status_force_reload(self):
        """Test getting license status with force reload."""
        future_date = (datetime.now() + timedelta(days=365)).strftime('%Y-%m-%d')
        license = License(
            company="Test Company",
            expires=future_date,
            allowed_machines=5,
            version="1.0.0"
        )
        
        private_key, public_key = generate_key_pair()
        sign_license(license, private_key)
        
        manager = LicenseManager(app_version="1.0.0")
        
        with patch.object(manager, 'load_license', return_value=license):
            with patch('pdf_merger.licensing.license_manager.get_embedded_public_key', return_value=public_key):
                manager.get_license_status()
                manager.get_license_status(force_reload=True)
                
                # Should load twice due to force_reload
                assert manager.load_license.call_count == 2
    
    def test_is_license_valid(self):
        """Test checking if license is valid."""
        future_date = (datetime.now() + timedelta(days=365)).strftime('%Y-%m-%d')
        license = License(
            company="Test Company",
            expires=future_date,
            allowed_machines=5,
            version="1.0.0"
        )
        
        private_key, public_key = generate_key_pair()
        sign_license(license, private_key)
        
        manager = LicenseManager(app_version="1.0.0")
        
        with patch.object(manager, 'get_license_status', return_value=LicenseStatus.VALID):
            result = manager.is_license_valid()
            
            assert result is True
        
        with patch.object(manager, 'get_license_status', return_value=LicenseStatus.EXPIRED):
            result = manager.is_license_valid()
            
            assert result is False
    
    def test_get_license_error_message(self):
        """Test getting error messages for license statuses."""
        manager = LicenseManager()
        
        messages = {
            LicenseStatus.VALID: manager.get_license_error_message(LicenseStatus.VALID),
            LicenseStatus.EXPIRED: manager.get_license_error_message(LicenseStatus.EXPIRED),
            LicenseStatus.INVALID_SIGNATURE: manager.get_license_error_message(LicenseStatus.INVALID_SIGNATURE),
            LicenseStatus.NOT_FOUND: manager.get_license_error_message(LicenseStatus.NOT_FOUND),
        }
        
        assert "valid" in messages[LicenseStatus.VALID].lower()
        assert "expired" in messages[LicenseStatus.EXPIRED].lower()
        assert "signature" in messages[LicenseStatus.INVALID_SIGNATURE].lower()
        assert "not found" in messages[LicenseStatus.NOT_FOUND].lower()
    
    def test_get_license_info(self):
        """Test getting license information."""
        future_date = (datetime.now() + timedelta(days=365)).strftime('%Y-%m-%d')
        license = License(
            company="Test Company",
            expires=future_date,
            allowed_machines=5,
            version="1.0.0"
        )
        
        manager = LicenseManager()
        
        with patch.object(manager, 'is_license_valid', return_value=True):
            with patch.object(manager, 'load_license', return_value=license):
                result = manager.get_license_info()
                
                assert result is not None
                assert result['company'] == "Test Company"
                assert result['expires'] == future_date
                assert result['allowed_machines'] == 5
    
    def test_get_license_info_invalid(self):
        """Test getting license info when license is invalid."""
        manager = LicenseManager()
        
        with patch.object(manager, 'is_license_valid', return_value=False):
            result = manager.get_license_info()
            
            assert result is None
    
    def test_get_license_info_no_license(self):
        """Test getting license info when license is None."""
        manager = LicenseManager()
        
        with patch.object(manager, 'is_license_valid', return_value=True):
            with patch.object(manager, 'load_license', return_value=None):
                result = manager.get_license_info()
                
                assert result is None
