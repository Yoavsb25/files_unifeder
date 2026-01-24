"""
Unit tests for licensing module __init__.
"""

import pytest

# Try to import, skip if cryptography not available
try:
    from pdf_merger.licensing import LicenseManager, LicenseStatus, License
    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False
    LicenseManager = None
    LicenseStatus = None
    License = None

pytestmark = pytest.mark.skipif(
    not CRYPTOGRAPHY_AVAILABLE,
    reason="cryptography module not available"
)


def test_licensing_exports():
    """Test that licensing module exports expected classes."""
    assert LicenseManager is not None
    assert LicenseStatus is not None
    assert License is not None
    
    # Test LicenseManager can be instantiated
    manager = LicenseManager()
    assert manager is not None
    
    # Test LicenseStatus enum values
    assert LicenseStatus.VALID is not None
    assert LicenseStatus.EXPIRED is not None
    assert LicenseStatus.INVALID_SIGNATURE is not None
    assert LicenseStatus.NOT_FOUND is not None
