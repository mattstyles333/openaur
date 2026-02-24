import re
import subprocess


class PackageManager:
    """Arch Linux package manager wrapper."""

    def __init__(self):
        self.yay_path = self._find_yay()

    def _find_yay(self) -> str | None:
        """Find yay binary path."""
        import shutil

        yay = shutil.which("yay")
        # Only return yay if it's actually the yay AUR helper
        # Don't return aura-pkg-add or other install scripts
        if yay and "aura-pkg-add" not in yay:
            return yay
        return None

    def search_packages(self, query: str, limit: int = 20) -> list[dict]:
        """Search for packages using yay."""
        try:
            if not self.yay_path:
                # Fallback to pacman
                result = subprocess.run(
                    ["pacman", "-Ss", query], capture_output=True, text=True, timeout=30
                )
            else:
                result = subprocess.run(
                    ["yay", "-Ss", "--limit", str(limit), query],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )

            if result.returncode != 0:
                return []

            return self._parse_search_results(result.stdout)
        except Exception as e:
            print(f"Error searching packages: {e}")
            return []

    def _parse_search_results(self, output: str) -> list[dict]:
        """Parse yay/pacman search output."""
        packages = []
        lines = output.strip().split("\n")

        i = 0
        while i < len(lines):
            line = lines[i]

            # Match package line: "extra/docker 1:29.2.1-1" or "aur/package 1.0.0-1"
            # Format: repo/name version
            match = re.match(r"^(\S+)/(\S+)\s+(\S+)$", line)

            if match:
                repo = match.group(1)
                name = match.group(2)
                version = match.group(3)
                description = ""

                # Check next line for description
                if i + 1 < len(lines) and lines[i + 1].strip().startswith("    "):
                    description = lines[i + 1].strip()
                    i += 1

                source = "aur" if repo == "aur" else "official"

                packages.append(
                    {
                        "name": name,
                        "version": version,
                        "source": source,
                        "description": description[:200],
                    }
                )

            i += 1

        return packages

    def install_package(self, package: str) -> dict:
        """Install a package using aura-pkg-add."""
        try:
            result = subprocess.run(
                ["aura-pkg-add", package], capture_output=True, text=True, timeout=300
            )

            success = result.returncode == 0

            # Combine stdout and stderr for error messages
            output = result.stdout
            if not success and not output:
                output = result.stderr
            if not output:
                output = "Unknown error"

            return {
                "success": success,
                "package": package,
                "output": output,
                "source": self._detect_source(result.stdout) if success else "unknown",
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "package": package,
                "error": "Installation timed out",
            }
        except Exception as e:
            return {"success": False, "package": package, "error": str(e)}

    def _detect_source(self, output: str) -> str:
        """Detect if package came from official repos or AUR."""
        if "aur" in output.lower() or "AUR" in output:
            return "aur"
        return "official"

    def remove_package(self, package: str) -> dict:
        """Remove a package."""
        try:
            result = subprocess.run(
                ["sudo", "pacman", "-R", "--noconfirm", package],
                capture_output=True,
                text=True,
                timeout=60,
            )

            return {
                "success": result.returncode == 0,
                "package": package,
                "output": result.stdout if result.returncode == 0 else result.stderr,
            }
        except Exception as e:
            return {"success": False, "package": package, "error": str(e)}

    def cleanup_unused(self) -> dict:
        """Remove unused packages."""
        try:
            result = subprocess.run(
                [
                    "sudo",
                    "pacman",
                    "-Rns",
                    "$(pacman",
                    "-Qtdq)",
                    "2>/dev/null",
                    "||",
                    "true",
                ],
                shell=True,
                capture_output=True,
                text=True,
                timeout=60,
            )

            return {
                "success": True,
                "message": "Cleanup completed",
                "output": result.stdout,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
