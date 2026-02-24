## Releasing openaur

This document describes how to create a new release of openaur.

### Version Numbering

We follow [Semantic Versioning](https://semver.org/):
- `MAJOR.MINOR.PATCH` (e.g., `1.2.3`)
- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes

### Creating a Release

#### Option 1: Using GitHub CLI (Recommended)

```bash
# Create a new tag and push it
git tag -a v1.0.1 -m "Release version 1.0.1"
git push origin v1.0.1
```

The GitHub Actions workflow will automatically:
- Create a GitHub Release
- Build and push Docker images to ghcr.io
- Generate release notes from commits

#### Option 2: Manual Release

1. Update CHANGELOG.md
2. Create a tag: `git tag -a v1.0.1 -m "Release version 1.0.1"`
3. Push tag: `git push origin v1.0.1`
4. Go to GitHub → Releases → Create release from tag

### Pre-releases

For beta/alpha versions:

```bash
git tag -a v1.1.0-beta.1 -m "Beta release 1.1.0-beta.1"
git push origin v1.1.0-beta.1
```

These will be marked as pre-releases on GitHub.

### After Release

Docker images are automatically published to:
```
ghcr.io/mattstyles333/openaur:v1.0.1
ghcr.io/mattstyles333/openaur:v1.0
ghcr.io/mattstyles333/openaur:v1
ghcr.io/mattstyles333/openaur:latest
```

Users can pull the release:
```bash
docker pull ghcr.io/mattstyles333/openaur:v1.0.1
```
