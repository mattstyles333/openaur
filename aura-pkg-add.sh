#!/bin/bash

set -euo pipefail

PACKAGE="${1:-}"
DRY_RUN="${2:-}"

if [[ -z "$PACKAGE" ]]; then
    echo "Usage: aura-pkg-add <package-name> [--dry-run]"
    exit 1
fi

if pacman -Qi "$PACKAGE" &>/dev/null || yay -Qi "$PACKAGE" &>/dev/null; then
    echo "✓ $PACKAGE is already installed"
    exit 0
fi

echo "📦 Installing $PACKAGE..."

if [[ "$DRY_RUN" == "--dry-run" ]]; then
    echo "Would install: $PACKAGE"
    yay -Si "$PACKAGE" 2>/dev/null || pacman -Si "$PACKAGE" 2>/dev/null || echo "Package not found in repos or AUR"
    exit 0
fi

if ! command -v yay &>/dev/null; then
    echo "Error: yay not found. Cannot install AUR packages."
    exit 1
fi

# Check if package exists in repos or AUR before installing
if ! yay -Si "$PACKAGE" &>/dev/null && ! pacman -Si "$PACKAGE" &>/dev/null; then
    echo "Error: Package '$PACKAGE' not found in repositories or AUR"
    exit 1
fi

# Install and capture exit code
yay -S --noconfirm --needed --noprogressbar \
    "$PACKAGE" 2>&1 | tee -a /tmp/aura-pkg-install.log

YAY_EXIT=${PIPESTATUS[0]}

if [[ $YAY_EXIT -eq 0 ]]; then
    echo "✓ $PACKAGE installed successfully"
    exit 0
else
    echo "Error: Failed to install $PACKAGE (exit code: $YAY_EXIT)"
    exit 1
fi
