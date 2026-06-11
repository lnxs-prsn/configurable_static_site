#!/usr/bin/env bash
set -e

# Tusmo ry — Build script for Linux/macOS
# Defensive checks + Tailwind binary auto-download

echo "=== Tusmo ry Build ==="

# Check 1: Python 3
if ! python3 --version >/dev/null 2>&1; then
    echo "ERROR: Python 3 is required but not found."
    echo "Install Python 3 and try again."
    exit 1
fi
echo "✓ Python 3 found"

# Check 2: Python dependencies
if ! python3 -c "import jinja2, yaml, markdown" >/dev/null 2>&1; then
    echo "ERROR: Required Python packages are missing."
    echo "Run: pip install -r requirements.txt"
    exit 1
fi
echo "✓ Python dependencies OK"

# Check 3: Tailwind CSS binary
tailwind_bin="bin/tailwindcss"
if [ ! -f "$tailwind_bin" ]; then
    echo "Tailwind binary not found. Downloading..."

    # Detect platform
    platform=""
    case "$(uname -s)" in
        Linux*)     platform="linux";;
        Darwin*)    platform="macos";;
        *)          echo "WARNING: Unknown platform. Please download Tailwind manually."; exit 1;;
    esac

    # Detect architecture
    arch=""
    case "$(uname -m)" in
        x86_64)   arch="x64";;
        arm64|aarch64) arch="arm64";;
        *)        echo "WARNING: Unknown architecture. Please download Tailwind manually."; exit 1;;
    esac

    # Pinned Tailwind v4 version
    tailwind_version="v4.0.4"
    download_url="https://github.com/tailwindlabs/tailwindcss/releases/download/${tailwind_version}/tailwindcss-${platform}-${arch}"

    echo "Downloading: ${download_url}"
    mkdir -p bin
    if ! curl -sL -o "$tailwind_bin" "$download_url"; then
        echo "ERROR: Failed to download Tailwind binary."
        echo "Download manually from: https://github.com/tailwindlabs/tailwindcss/releases"
        exit 1
    fi
    chmod +x "$tailwind_bin"
    echo "✓ Tailwind binary downloaded"
else
    echo "✓ Tailwind binary found"
fi

# Run the build
echo ""
echo "Building site..."
python3 build.py

echo ""
echo "=== Build complete ==="
echo "Output is in output/"
echo "Preview: python3 -m http.server 8000 --directory output/"
