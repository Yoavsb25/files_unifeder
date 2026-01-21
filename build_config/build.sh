#!/bin/bash
# Build script for macOS

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

echo -e "${GREEN}Building PDF Batch Merger for macOS...${NC}"
echo "Project root: $PROJECT_ROOT"
echo ""

# Check if PyInstaller is installed
if ! command -v pyinstaller &> /dev/null; then
    echo -e "${RED}Error: PyInstaller is not installed${NC}"
    echo "Install it with: pip install pyinstaller"
    exit 1
fi

# Check if public key exists
PUBLIC_KEY="$PROJECT_ROOT/pdf_merger/licensing/public_key.pem"
if [ ! -f "$PUBLIC_KEY" ]; then
    echo -e "${YELLOW}Warning: Public key not found at $PUBLIC_KEY${NC}"
    echo "The app will still build, but license verification may not work."
    echo ""
fi

# Change to project root
cd "$PROJECT_ROOT"

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf build/
rm -rf dist/
rm -rf "PDF Batch Merger.app"

# Build with PyInstaller
echo ""
echo "Building application..."
pyinstaller build_config/macos.spec

# Check if build succeeded
if [ -d "dist/PDF Batch Merger.app" ]; then
    echo ""
    echo -e "${GREEN}✓ Build successful!${NC}"
    echo "Application bundle: dist/PDF Batch Merger.app"
    echo ""
    echo "To test the app, run:"
    echo "  open 'dist/PDF Batch Merger.app'"
else
    echo ""
    echo -e "${RED}✗ Build failed!${NC}"
    exit 1
fi
