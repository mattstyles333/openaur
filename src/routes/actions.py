from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List

from src.models.database import get_db, ActionRegistry
from src.models.schemas import ActionCreateRequest, ActionTreeNode
from src.services.doc_crawler import DocCrawler
from src.utils.yaml_registry import YamlRegistry

router = APIRouter()


@router.post("/")
async def create_action(request: ActionCreateRequest, db: Session = Depends(get_db)):
    """Register a new binary action."""
    try:
        # Check if binary exists
        import shutil

        if not shutil.which(request.binary):
            raise HTTPException(
                status_code=404, detail=f"Binary {request.binary} not found"
            )

        # Crawl documentation
        crawler = DocCrawler()
        tree = crawler.crawl(request.binary, max_depth=12)

        # Save to YAML
        yaml_reg = YamlRegistry()
        yaml_path = yaml_reg.save_action(request.binary, tree, request.safety)

        # Save to database
        action = ActionRegistry(
            id=request.binary,
            binary_path=shutil.which(request.binary),
            yaml_path=yaml_path,
            safety_level=request.safety,
            description=tree.get("description", ""),
        )
        db.add(action)
        db.commit()

        if request.auto_index:
            # Index to OpenMemory (async)
            pass

        return {
            "id": action.id,
            "binary": request.binary,
            "yaml_path": yaml_path,
            "commands_count": len(tree.get("tree", {})),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def list_actions(db: Session = Depends(get_db)):
    """List all registered actions."""
    actions = db.query(ActionRegistry).all()
    return [
        {
            "id": a.id,
            "binary": a.binary_path,
            "safety": a.safety_level,
            "description": a.description,
            "indexed_at": a.indexed_at,
        }
        for a in actions
    ]


@router.get("/{action_id}")
async def get_action(action_id: str, db: Session = Depends(get_db)):
    """Get action details."""
    action = db.query(ActionRegistry).filter(ActionRegistry.id == action_id).first()
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")

    # Load YAML tree
    yaml_reg = YamlRegistry()
    tree = yaml_reg.load_action(action_id)

    return {
        "id": action.id,
        "binary": action.binary_path,
        "safety": action.safety_level,
        "description": action.description,
        "tree": tree.get("tree", {}),
    }


@router.get("/{action_id}/tree")
async def get_action_tree(action_id: str, depth: int = 2):
    """Get command tree for an action (progressive disclosure)."""
    yaml_reg = YamlRegistry()
    tree = yaml_reg.load_action(action_id)

    if not tree:
        raise HTTPException(status_code=404, detail="Action tree not found")

    # Return only requested depth
    def truncate_tree(node, current_depth=0):
        if current_depth >= depth:
            return {}

        result = {
            "description": node.get("description", ""),
            "safety": node.get("safety", 1),
        }

        if "subcommands" in node and current_depth < depth - 1:
            result["subcommands"] = {
                k: truncate_tree(v, current_depth + 1)
                for k, v in list(node["subcommands"].items())[:10]  # Limit to 10
            }

        return result

    truncated = {
        k: truncate_tree(v)
        for k, v in list(tree.get("tree", {}).items())[:20]  # Limit root commands
    }

    return {"action": action_id, "tree": truncated, "depth": depth}


@router.post("/{action_id}/index")
async def index_action(action_id: str, db: Session = Depends(get_db)):
    """Index action to OpenMemory."""
    # TODO: Implement OpenMemory indexing
    return {"message": "Indexing started", "action_id": action_id}
