#!/bin/bash
# macOS Notarization Script
# Signs and notarizes the macOS application bundle

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
APP_PATH=""
APPLE_ID=""
TEAM_ID=""
PASSWORD=""
CERTIFICATE_NAME="Developer ID Application"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --app)
            APP_PATH="$2"
            shift 2
            ;;
        --apple-id)
            APPLE_ID="$2"
            shift 2
            ;;
        --team-id)
            TEAM_ID="$2"
            shift 2
            ;;
        --password)
            PASSWORD="$2"
            shift 2
            ;;
        --certificate)
            CERTIFICATE_NAME="$2"
            shift 2
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

# Validate required arguments
if [ -z "$APP_PATH" ]; then
    echo -e "${RED}Error: --app path is required${NC}"
    exit 1
fi

if [ -z "$APPLE_ID" ]; then
    echo -e "${RED}Error: --apple-id is required${NC}"
    exit 1
fi

if [ -z "$TEAM_ID" ]; then
    echo -e "${RED}Error: --team-id is required${NC}"
    exit 1
fi

if [ -z "$PASSWORD" ]; then
    echo -e "${RED}Error: --password is required${NC}"
    exit 1
fi

# Check if app exists
if [ ! -d "$APP_PATH" ]; then
    echo -e "${RED}Error: App bundle not found at $APP_PATH${NC}"
    exit 1
fi

echo -e "${GREEN}Starting macOS code signing and notarization...${NC}"
echo ""

# Step 1: Code Sign
echo -e "${YELLOW}Step 1: Code signing application...${NC}"
codesign --force --deep --sign "$CERTIFICATE_NAME" "$APP_PATH"

if [ $? -ne 0 ]; then
    echo -e "${RED}Code signing failed${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Code signing successful${NC}"
echo ""

# Step 2: Verify signing
echo -e "${YELLOW}Step 2: Verifying code signature...${NC}"
codesign --verify --verbose "$APP_PATH"

if [ $? -ne 0 ]; then
    echo -e "${RED}Code signature verification failed${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Code signature verified${NC}"
echo ""

# Step 3: Create zip for notarization
echo -e "${YELLOW}Step 3: Creating zip archive for notarization...${NC}"
ZIP_PATH="${APP_PATH%.app}.zip"
ditto -c -k --keepParent "$APP_PATH" "$ZIP_PATH"

if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to create zip archive${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Zip archive created: $ZIP_PATH${NC}"
echo ""

# Step 4: Submit for notarization
echo -e "${YELLOW}Step 4: Submitting for notarization...${NC}"
echo "This may take several minutes..."

xcrun notarytool submit "$ZIP_PATH" \
    --apple-id "$APPLE_ID" \
    --team-id "$TEAM_ID" \
    --password "$PASSWORD" \
    --wait

if [ $? -ne 0 ]; then
    echo -e "${RED}Notarization failed${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Notarization successful${NC}"
echo ""

# Step 5: Staple notarization ticket
echo -e "${YELLOW}Step 5: Stapling notarization ticket...${NC}"
xcrun stapler staple "$APP_PATH"

if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to staple notarization ticket${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Notarization ticket stapled${NC}"
echo ""

# Step 6: Final verification
echo -e "${YELLOW}Step 6: Final verification...${NC}"
spctl --assess --verbose "$APP_PATH"

if [ $? -ne 0 ]; then
    echo -e "${YELLOW}Warning: Gatekeeper assessment failed (this may be normal for development)${NC}"
else
    echo -e "${GREEN}✓ Gatekeeper assessment passed${NC}"
fi

echo ""
echo -e "${GREEN}✓ Notarization complete!${NC}"
echo "App bundle: $APP_PATH"
echo "Zip archive: $ZIP_PATH"
