import shutil
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.models.database import get_db
from src.services.doc_crawler import DocCrawler
from src.utils.yaml_registry import YamlRegistry

router = APIRouter()


@router.post("/action")
async def ingest_action(
    binary: str, safety: int = 2, max_depth: int = 12, db: Session = Depends(get_db)
) -> dict[str, Any]:
    """
    Ingest a CLI tool's documentation into the action registry.

    This crawls the binary's --help output using BFS and stores it in YAML.
    """
    try:
        # Check if binary exists
        binary_path = shutil.which(binary)
        if not binary_path:
            raise HTTPException(status_code=404, detail=f"Binary {binary} not found")

        # Crawl documentation
        crawler = DocCrawler()
        tree = crawler.crawl(binary, max_depth=max_depth)

        # Save to YAML
        yaml_reg = YamlRegistry()
        yaml_path = yaml_reg.save_action(binary, tree, safety)

        # Import models here to avoid circular imports
        from src.models.database import ActionRegistry

        # Check if already exists
        existing = db.query(ActionRegistry).filter(ActionRegistry.id == binary).first()

        if existing:
            # Update existing
            existing.binary_path = binary_path
            existing.yaml_path = yaml_path
            existing.safety_level = safety
            existing.description = tree.get("description", "")
            existing.indexed_at = datetime.utcnow()
            db.commit()

            return {
                "message": f"Updated {binary} action registry",
                "binary": binary,
                "path": yaml_path,
                "commands_count": len(tree.get("tree", {})),
                "safety": safety,
                "status": "updated",
            }
        else:
            # Create new
            action = ActionRegistry(
                id=binary,
                binary_path=binary_path,
                yaml_path=yaml_path,
                safety_level=safety,
                description=tree.get("description", ""),
            )
            db.add(action)
            db.commit()

            return {
                "message": f"Ingested {binary} into action registry",
                "binary": binary,
                "path": yaml_path,
                "commands_count": len(tree.get("tree", {})),
                "safety": safety,
                "status": "created",
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class MemoryIngestRequest(BaseModel):
    content: str
    source: str = "manual"
    tags: list[str] | None = None
    metadata: dict | None = None


@router.post("/memory")
async def ingest_memory(request: MemoryIngestRequest) -> dict[str, Any]:
    """
    Ingest a memory into OpenMemory.

    Store a memory for future context retrieval.
    """
    try:
        from src.services.openmemory import get_memory

        memory_service = get_memory()

        # Actually store the memory
        result = await memory_service.store(
            content=request.content,
            memory_type="manual",
            importance=0.8,
            tags=request.tags or [],
            metadata={"source": request.source, **(request.metadata or {})},
            user_id="default",
        )

        return {
            "message": "Memory ingested successfully",
            "content_preview": request.content[:100] + "..." if len(request.content) > 100 else request.content,
            "source": request.source,
            "tags": request.tags or [],
            "metadata": request.metadata or {},
            "memory_id": result.get("id", "unknown"),
            "timestamp": datetime.utcnow().isoformat(),
            "status": "stored",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/emails")
async def ingest_emails(
    source: str = "sent", provider: str = "gmail", retention_days: int = 90
) -> dict[str, Any]:
    """
    Ingest emails for empathy context.

    Sources: sent, inbox
    Providers: gmail, imap
    """
    try:
        # Placeholder for email ingestion
        # Would integrate with gogcli or offlineimap
        return {
            "message": f"Email ingestion initiated from {source}",
            "provider": provider,
            "source": source,
            "retention_days": retention_days,
            "status": "started",
            "note": "Email ingestion not yet implemented - requires OAuth setup",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def ingest_status() -> dict[str, Any]:
    """
    Get ingestion status and statistics.
    """
    try:
        yaml_reg = YamlRegistry()
        actions = yaml_reg.list_actions()

        return {
            "status": "ready",
            "ingested_actions": len(actions),
            "actions": [a["binary"] for a in actions],
            "capabilities": [
                "action - CLI documentation",
                "memory - Manual memories",
                "emails - Email context (placeholder)",
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
