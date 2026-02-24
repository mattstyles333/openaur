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

yay -S --noconfirm --needed --nocheck --noprogressbar \
    --pgpfetch --pgpflags "no-check" \
    "$PACKAGE" 2>&1 | tee -a /tmp/aura-pkg-install.log

echo "✓ $PACKAGE installed successfully"

exit 0
