import re
import subprocess
from collections import deque


class DocCrawler:
    """BFS crawler for CLI command documentation."""

    def __init__(self):
        self.max_depth = 12
        self.visited = set()

    def crawl(self, binary: str, max_depth: int = 12) -> dict:
        """Crawl command documentation using BFS."""
        self.max_depth = max_depth
        self.visited = set()

        # Check binary exists
        import shutil

        binary_path = shutil.which(binary)
        if not binary_path:
            raise ValueError(f"Binary {binary} not found")

        # Start with root help
        tree = {
            "binary": binary,
            "binary_path": binary_path,
            "description": self._get_description(binary),
            "tree": {},
        }

        # BFS crawl
        queue = deque([(binary, [], 0)])

        while queue:
            cmd_path, parent_chain, depth = queue.popleft()

            if depth >= max_depth:
                continue

            cmd_id = " ".join([binary] + parent_chain + [cmd_path])
            if cmd_id in self.visited:
                continue

            self.visited.add(cmd_id)

            # Get help output
            help_text = self._get_help(cmd_id)
            if not help_text:
                continue

            # Parse subcommands
            subcommands = self._parse_subcommands(help_text)

            # Build tree node
            node = {
                "description": self._extract_description(help_text),
                "safety": self._detect_safety_level(help_text),
                "args": self._parse_args(help_text),
            }

            if subcommands and depth < max_depth - 1:
                node["subcommands"] = {}
                for subcmd in subcommands[:20]:  # Limit to 20 subcommands
                    queue.append(
                        (
                            subcmd,
                            parent_chain + [cmd_path]
                            if cmd_path != binary
                            else [cmd_path],
                            depth + 1,
                        )
                    )

            # Insert into tree
            self._insert_into_tree(tree["tree"], parent_chain, cmd_path, node)

        return tree

    def _get_help(self, cmd: str) -> str:
        """Get help output for a command."""
        try:
            result = subprocess.run(
                f"{cmd} --help", shell=True, capture_output=True, text=True, timeout=10
            )
            return result.stdout + result.stderr
        except:
            return ""

    def _get_description(self, binary: str) -> str:
        """Get binary description."""
        try:
            # Try man page first
            result = subprocess.run(
                f"man {binary} 2>/dev/null | head -20 || {binary} --help | head -10",
                shell=True,
                capture_output=True,
                text=True,
                timeout=5,
            )
            lines = result.stdout.strip().split("\n")
            for line in lines:
                if (
                    line
                    and not line.startswith("Usage")
                    and not line.startswith("usage")
                ):
                    return line.strip()[:200]
            return f"CLI tool: {binary}"
        except:
            return f"CLI tool: {binary}"

    def _parse_subcommands(self, help_text: str) -> list[str]:
        """Extract subcommands from help text."""
        subcommands = []

        # Common patterns for subcommands section
        patterns = [
            r"Commands:[\s\n]+((?:\s+[a-z-]+.*?\n)+)",
            r"COMMANDS[\s\n]+((?:\s+[a-z-]+.*?\n)+)",
            r"Available commands:[\s\n]+((?:\s+[a-z-]+.*?\n)+)",
            r"Common commands:[\s\n]+((?:\s+[a-z-]+.*?\n)+)",
            r"^[\s]*([a-z][a-z0-9-]+)\s{2,}",  # Indented command names
        ]

        for pattern in patterns:
            matches = re.findall(pattern, help_text, re.MULTILINE | re.IGNORECASE)
            if matches:
                if isinstance(matches[0], str):
                    # Extract individual commands from block
                    cmd_lines = matches[0].strip().split("\n")
                    for line in cmd_lines[:30]:  # Limit parsing
                        cmd = line.strip().split()[0] if line.strip() else ""
                        if cmd and re.match(r"^[a-z][a-z0-9-]*$", cmd):
                            subcommands.append(cmd)
                break

        return list(set(subcommands))[:20]  # Deduplicate and limit

    def _extract_description(self, help_text: str) -> str:
        """Extract description from help text."""
        lines = help_text.strip().split("\n")
        for line in lines[1:10]:  # Skip first line (usually usage)
            line = line.strip()
            if line and not line.startswith("-") and not line.startswith("Usage"):
                return line[:200]
        return "No description available"

    def _detect_safety_level(self, help_text: str) -> int:
        """Detect safety level (1-3) from help text."""
        dangerous = [
            "delete",
            "remove",
            "rm",
            "destroy",
            "kill",
            "force",
            "-f",
            "--force",
        ]
        write_ops = ["create", "add", "update", "modify", "write", "push", "commit"]

        help_lower = help_text.lower()

        for d in dangerous:
            if d in help_lower:
                return 3  # Destructive

        for w in write_ops:
            if w in help_lower:
                return 2  # Write

        return 1  # Read-only

    def _parse_args(self, help_text: str) -> dict[str, str]:
        """Parse arguments from help text."""
        args = {}

        # Match option patterns
        patterns = [
            r"\s+(-[a-zA-Z],?\s+--[a-z-]+)\s+(.*?)\n",
            r"\s+(--[a-z-]+)\s+(.*?)\n",
            r"\s+(-[a-zA-Z])\s+(.*?)\n",
        ]

        for pattern in patterns:
            matches = re.findall(pattern, help_text, re.MULTILINE)
            for flag, desc in matches[:10]:
                args[flag.strip()] = desc.strip()[:100]

        return args

    def _insert_into_tree(
        self, tree: dict, parent_chain: list[str], cmd: str, node: dict
    ):
        """Insert node into tree at correct location."""
        current = tree

        if not parent_chain:
            # Root level
            current[cmd] = node
            return

        # Navigate to parent
        for parent in parent_chain:
            if parent not in current:
                current[parent] = {"subcommands": {}}
            if "subcommands" not in current[parent]:
                current[parent]["subcommands"] = {}
            current = current[parent]["subcommands"]

        current[cmd] = node
