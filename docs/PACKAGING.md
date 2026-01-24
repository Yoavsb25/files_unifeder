# Packaging, Signing, and Notarization Guide

This guide covers the process of packaging, code signing, and notarizing PDF Batch Merger for distribution on macOS and Windows.

## Overview

- **macOS**: Requires code signing and notarization for distribution outside the App Store
- **Windows**: Requires code signing with a valid certificate for distribution

## Prerequisites

### macOS

- Apple Developer account (paid membership required)
- Xcode Command Line Tools installed
- Valid code signing certificate
- App-specific password for notarization

### Windows

- Code signing certificate (purchased from a Certificate Authority)
- `signtool.exe` (included with Windows SDK)
- Certificate stored in Windows Certificate Store or as a .pfx file

## macOS Packaging and Notarization

### Step 1: Code Signing

1. **Obtain a Developer ID Application certificate**:
   - Log in to [Apple Developer Portal](https://developer.apple.com)
   - Navigate to Certificates, Identifiers & Profiles
   - Create a "Developer ID Application" certificate
   - Download and install in Keychain Access

2. **Sign the application**:
   ```bash
   codesign --force --deep --sign "Developer ID Application: Your Name (TEAM_ID)" \
     "dist/PDF Batch Merger.app"
   ```

3. **Verify signing**:
   ```bash
   codesign --verify --verbose "dist/PDF Batch Merger.app"
   spctl --assess --verbose "dist/PDF Batch Merger.app"
   ```

### Step 2: Notarization

1. **Create an app-specific password**:
   - Go to [Apple ID Account](https://appleid.apple.com)
   - Generate an app-specific password for notarization

2. **Submit for notarization**:
   ```bash
   xcrun notarytool submit "dist/PDF Batch Merger.zip" \
     --apple-id "your@email.com" \
     --team-id "TEAM_ID" \
     --password "app-specific-password" \
     --wait
   ```

3. **Staple the notarization ticket**:
   ```bash
   xcrun stapler staple "dist/PDF Batch Merger.app"
   ```

### Step 3: Automated Script

Use the provided `build_config/notarize.sh` script:

```bash
./build_config/notarize.sh \
  --app "dist/PDF Batch Merger.app" \
  --apple-id "your@email.com" \
  --team-id "TEAM_ID" \
  --password "app-specific-password"
```

## Windows Code Signing

### Step 1: Obtain a Code Signing Certificate

1. Purchase a code signing certificate from a trusted CA (e.g., DigiCert, Sectigo)
2. Install the certificate in Windows Certificate Store or export as .pfx file

### Step 2: Sign the Executable

Using Certificate Store:
```cmd
signtool sign /f "certificate.pfx" /p "password" /t "http://timestamp.digicert.com" "dist\PDF Batch Merger.exe"
```

Using Certificate Store:
```cmd
signtool sign /a /t "http://timestamp.digicert.com" "dist\PDF Batch Merger.exe"
```

### Step 3: Verify Signing

```cmd
signtool verify /pa "dist\PDF Batch Merger.exe"
```

### Step 4: Automated Script

Use the provided `build_config/sign_windows.bat` script:

```cmd
build_config\sign_windows.bat "dist\PDF Batch Merger.exe" "certificate.pfx" "password"
```

## CI/CD Integration

### GitHub Actions - macOS

Add to `.github/workflows/build-macos.yml`:

```yaml
- name: Code Sign
  run: |
    codesign --force --deep --sign "${{ secrets.MACOS_CERTIFICATE }}" \
      "dist/PDF Batch Merger.app"

- name: Notarize
  run: |
    xcrun notarytool submit "dist/PDF Batch Merger.zip" \
      --apple-id "${{ secrets.APPLE_ID }}" \
      --team-id "${{ secrets.TEAM_ID }}" \
      --password "${{ secrets.APP_SPECIFIC_PASSWORD }}" \
      --wait
    xcrun stapler staple "dist/PDF Batch Merger.app"
```

### GitHub Actions - Windows

Add to `.github/workflows/build-windows.yml`:

```yaml
- name: Code Sign
  run: |
    signtool sign /f "${{ secrets.WINDOWS_CERT_PFX }}" \
      /p "${{ secrets.WINDOWS_CERT_PASSWORD }}" \
      /t "http://timestamp.digicert.com" \
      "dist\PDF Batch Merger.exe"
```

## Certificate Management

### macOS Keychain Setup

1. Install certificate in Keychain Access
2. Ensure certificate is in "login" keychain
3. Verify certificate is valid and not expired

### Windows Certificate Store

1. Import .pfx file:
   ```cmd
   certutil -importPFX "certificate.pfx"
   ```
2. Or use Certificate Manager (certmgr.msc)

## Troubleshooting

### macOS

**"No valid signing certificate found"**
- Verify certificate is installed in Keychain
- Check certificate expiration date
- Ensure using correct certificate type (Developer ID Application)

**Notarization fails**
- Check app-specific password is correct
- Verify Team ID matches certificate
- Check for hardened runtime requirements

**"App is damaged" error**
- Ensure notarization ticket is stapled
- Verify code signing is valid
- Check Gatekeeper settings

### Windows

**"No certificate found"**
- Verify certificate is in Certificate Store
- Check certificate is valid and not expired
- Ensure using correct certificate store location

**Timestamp server errors**
- Try alternative timestamp servers:
  - `http://timestamp.digicert.com`
  - `http://timestamp.verisign.com/scripts/timstamp.dll`
  - `http://timestamp.globalsign.com/scripts/timstamp.dll`

## Security Best Practices

1. **Never commit certificates or passwords** to version control
2. **Use secrets management** in CI/CD (GitHub Secrets, etc.)
3. **Rotate certificates** before expiration
4. **Store certificates securely** (encrypted, access-controlled)
5. **Use app-specific passwords** for notarization (not main Apple ID password)

## Additional Resources

- [Apple Code Signing Guide](https://developer.apple.com/documentation/security/code_signing_services)
- [Apple Notarization Guide](https://developer.apple.com/documentation/security/notarizing_macos_software_before_distribution)
- [Windows Code Signing](https://docs.microsoft.com/en-us/windows/win32/win_cert/code-signing)
- [DigiCert Code Signing](https://www.digicert.com/code-signing/)
