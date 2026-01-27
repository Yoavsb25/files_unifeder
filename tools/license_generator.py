#!/usr/bin/env python3
"""
License Generator Tool
Generates signed license files for PDF Batch Merger.

Usage:
    python tools/license_generator.py --company "Company Name" --expires "2027-12-31" --machines 5
"""

import argparse
import sys
import io
from datetime import datetime
from pathlib import Path

# Fix Windows console encoding to support Unicode characters
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from pdf_merger import APP_VERSION
from pdf_merger.licensing.license_model import License
from pdf_merger.licensing.license_signer import (
    load_private_key,
    sign_license,
    save_private_key,
    save_public_key,
    generate_key_pair
)
from pdf_merger.utils.logging_utils import setup_logger, get_logger

# Setup logging
setup_logger("pdf_merger", level=20)
logger = get_logger("license_generator")


def generate_keys(output_dir: Path):
    """
    Generate a new key pair.
    
    Args:
        output_dir: Directory to save keys
    """
    print("Generating new RSA key pair...")
    private_key, public_key = generate_key_pair()
    
    private_key_path = output_dir / "private_key.pem"
    public_key_path = output_dir / "public_key.pem"
    
    if save_private_key(private_key, private_key_path):
        print(f"✓ Private key saved to: {private_key_path}")
        print(f"  WARNING: Keep this key secure and never share it!")
    else:
        print(f"✗ Failed to save private key")
        return False
    
    if save_public_key(public_key, public_key_path):
        print(f"✓ Public key saved to: {public_key_path}")
        print(f"  This key should be embedded in the application.")
    else:
        print(f"✗ Failed to save public key")
        return False
    
    return True


def generate_license(
    company: str,
    expires: str,
    allowed_machines: int,
    version: str,
    private_key_path: Path,
    output_path: Path
) -> bool:
    """
    Generate a signed license file.
    
    Args:
        company: Company name
        expires: Expiration date (YYYY-MM-DD)
        allowed_machines: Number of allowed machines
        version: License version
        private_key_path: Path to private key
        output_path: Path to save license file
        
    Returns:
        True if successful
    """
    # Validate expiration date
    try:
        expiry_date = datetime.strptime(expires, '%Y-%m-%d').date()
        today = datetime.now().date()
        if expiry_date <= today:
            print(f"✗ Error: Expiration date must be in the future")
            return False
    except ValueError:
        print(f"✗ Error: Invalid date format. Use YYYY-MM-DD")
        return False
    
    # Load private key
    print(f"Loading private key from {private_key_path}...")
    private_key = load_private_key(private_key_path)
    if not private_key:
        print(f"✗ Error: Failed to load private key")
        return False
    
    # Create license
    license = License(
        company=company,
        expires=expires,
        allowed_machines=allowed_machines,
        version=version
    )
    
    # Sign license
    print("Signing license...")
    if not sign_license(license, private_key):
        print(f"✗ Error: Failed to sign license")
        return False
    
    # Save license
    if license.save_to_file(output_path):
        print(f"✓ License saved to: {output_path}")
        print(f"\nLicense Details:")
        print(f"  Company: {license.company}")
        print(f"  Expires: {license.expires}")
        print(f"  Allowed Machines: {license.allowed_machines}")
        print(f"  Version: {license.version}")
        return True
    else:
        print(f"✗ Error: Failed to save license")
        return False


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Generate signed license files for PDF Batch Merger"
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Generate keys command
    keys_parser = subparsers.add_parser('generate-keys', help='Generate new RSA key pair')
    keys_parser.add_argument(
        '--output-dir',
        type=Path,
        default=Path('tools'),
        help='Directory to save keys (default: tools/)'
    )
    
    # Generate license command
    license_parser = subparsers.add_parser('generate-license', help='Generate signed license')
    license_parser.add_argument(
        '--company',
        required=True,
        help='Company name'
    )
    license_parser.add_argument(
        '--expires',
        required=True,
        help='Expiration date (YYYY-MM-DD)'
    )
    license_parser.add_argument(
        '--machines',
        type=int,
        default=1,
        help='Number of allowed machines (default: 1)'
    )
    license_parser.add_argument(
        '--version',
        default=APP_VERSION,
        help=f'License version (default: {APP_VERSION})'
    )
    license_parser.add_argument(
        '--private-key',
        type=Path,
        default=Path('tools/private_key.pem'),
        help='Path to private key file (default: tools/private_key.pem)'
    )
    license_parser.add_argument(
        '--output',
        type=Path,
        default=Path('license.json'),
        help='Output license file path (default: license.json)'
    )
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    if args.command == 'generate-keys':
        if not generate_keys(args.output_dir):
            sys.exit(1)
    elif args.command == 'generate-license':
        if not generate_license(
            company=args.company,
            expires=args.expires,
            allowed_machines=args.machines,
            version=args.version,
            private_key_path=args.private_key,
            output_path=args.output
        ):
            sys.exit(1)


if __name__ == '__main__':
    main()
