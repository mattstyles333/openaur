import yaml
import os
from typing import Dict, Optional, Any
from pathlib import Path


class YamlRegistry:
    """YAML-based action registry handler."""

    def __init__(self, base_path: str = None):
        if base_path is None:
            base_path = os.path.join(
                os.path.dirname(__file__), "..", "..", "actions", "manifests"
            )

        self.base_path = Path(base_path).resolve()
        self.base_path.mkdir(parents=True, exist_ok=True)

    def save_action(self, binary: str, tree: Dict, safety: int = 2) -> str:
        """Save action tree to YAML file."""
        filename = f"{binary}.yaml"
        filepath = self.base_path / filename

        data = {
            "binary": binary,
            "binary_path": tree.get("binary_path", binary),
            "safety": safety,
            "description": tree.get("description", ""),
            "tree": tree.get("tree", {}),
            "metadata": {"version": "1.0", "format": "openaura-v1"},
        }

        with open(filepath, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

        return str(filepath)

    def load_action(self, binary: str) -> Optional[Dict]:
        """Load action tree from YAML file."""
        filename = f"{binary}.yaml"
        filepath = self.base_path / filename

        if not filepath.exists():
            return None

        with open(filepath, "r") as f:
            return yaml.safe_load(f)

    def list_actions(self) -> list:
        """List all registered actions."""
        actions = []

        for yaml_file in self.base_path.glob("*.yaml"):
            try:
                with open(yaml_file, "r") as f:
                    data = yaml.safe_load(f)
                    if data:
                        actions.append(
                            {
                                "binary": data.get("binary", yaml_file.stem),
                                "description": data.get("description", ""),
                                "safety": data.get("safety", 2),
                                "file": str(yaml_file),
                            }
                        )
            except Exception as e:
                print(f"Error loading {yaml_file}: {e}")

        return actions

    def get_tree_node(self, binary: str, path: list) -> Optional[Dict]:
        """Get specific node from tree by path."""
        tree = self.load_action(binary)
        if not tree:
            return None

        current = tree.get("tree", {})

        for key in path:
            if key in current:
                current = current[key]
            else:
                return None

        return current

    def update_action_metadata(self, binary: str, metadata: Dict) -> bool:
        """Update action metadata."""
        tree = self.load_action(binary)
        if not tree:
            return False

        tree["metadata"].update(metadata)

        filepath = self.base_path / f"{binary}.yaml"
        with open(filepath, "w") as f:
            yaml.dump(tree, f, default_flow_style=False, sort_keys=False)

        return True
