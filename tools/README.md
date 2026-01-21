# License Generation Tools

This directory contains tools for generating and managing licenses for PDF Batch Merger.

## Setup

### Step 1: Generate Key Pair

First, generate a new RSA key pair:

```bash
python tools/license_generator.py generate-keys --output-dir tools
```

This creates:
- `tools/private_key.pem` - **KEEP THIS SECRET!** Use this to sign licenses
- `tools/public_key.pem` - Embed this in the application for license verification

### Step 2: Embed Public Key

Copy `tools/public_key.pem` to `pdf_merger/licensing/public_key.pem`:

```bash
cp tools/public_key.pem pdf_merger/licensing/public_key.pem
```

The PyInstaller build process will automatically include this file in the packaged application.

**Important**: The public key can be safely included in the application. The private key must NEVER be included in the application or shared.

## Generating Licenses

### Generate a License

```bash
python tools/license_generator.py generate-license \
    --company "Smith & Co Law" \
    --expires "2027-12-31" \
    --machines 5 \
    --private-key tools/private_key.pem \
    --output license.json
```

### Parameters

- `--company`: Company name (required)
- `--expires`: Expiration date in YYYY-MM-DD format (required)
- `--machines`: Number of allowed machines (default: 1)
- `--version`: License version (default: matches app version)
- `--private-key`: Path to private key file (default: tools/private_key.pem)
- `--output`: Output license file path (default: license.json)

### Example

```bash
# Generate a license for a law firm, valid until end of 2027, for 3 machines
python tools/license_generator.py generate-license \
    --company "Johnson Legal Services" \
    --expires "2027-12-31" \
    --machines 3 \
    --output client_license.json
```

## Security Notes

1. **Private Key**: 
   - Store `private_key.pem` securely
   - Never commit it to version control (already in .gitignore)
   - Never share it with clients
   - Use it only on a secure machine to generate licenses

2. **Public Key**:
   - Safe to include in the application
   - Used by the app to verify license signatures
   - Cannot be used to generate licenses

3. **License Files**:
   - Each license is signed with the private key
   - The app verifies signatures using the embedded public key
   - Clients cannot modify licenses without invalidating the signature

## License File Structure

The generated `license.json` file contains:

```json
{
  "company": "Company Name",
  "expires": "2027-12-31",
  "allowed_machines": 5,
  "version": "1.0.0",
  "signature": "..."
}
```

The signature is a base64-encoded RSA signature of the license data (without the signature field itself).

## Distribution

1. Generate the license file using the tool above
2. Provide `license.json` to the client
3. Client places `license.json` in the application directory (or `~/.pdf_merger/` on macOS/Linux)
4. The application automatically validates the license on startup
