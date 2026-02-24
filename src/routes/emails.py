"""Email ingestion routes.

API endpoints for email synchronization and management.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime

from src.services.email_ingestion import EmailIngestionService

router = APIRouter()


class EmailSyncRequest(BaseModel):
    provider: str  # "gogcli" or "offlineimap"
    path: str


class EmailSearchRequest(BaseModel):
    query: str
    folder: Optional[str] = None
    since: Optional[datetime] = None
    is_sent: Optional[bool] = None
    limit: int = 50


class EmailResponse(BaseModel):
    id: str
    subject: str
    sender: str
    recipients: List[str]
    date: str
    folder: str
    is_sent: bool


@router.post("/sync")
async def sync_emails(request: EmailSyncRequest):
    """Sync emails from provider.

    Providers:
    - gogcli: Google Takeout path (e.g., /path/to/Takeout/Mail)
    - offlineimap: Maildir path (e.g., ~/Mail)
    """
    service = EmailIngestionService()

    if request.provider == "gogcli":
        result = await service.sync_gogcli(request.path)
    elif request.provider == "offlineimap":
        result = await service.sync_offlineimap(request.path)
    else:
        raise HTTPException(
            status_code=400, detail=f"Unknown provider: {request.provider}"
        )

    return result


@router.post("/search")
async def search_emails(request: EmailSearchRequest):
    """Search stored emails."""
    service = EmailIngestionService()

    emails = await service.search_emails(
        query=request.query,
        folder=request.folder,
        since=request.since,
        is_sent=request.is_sent,
    )

    return {
        "count": len(emails),
        "emails": [
            {
                "id": e.id,
                "subject": e.subject,
                "sender": e.sender,
                "recipients": e.recipients,
                "date": e.date.isoformat(),
                "folder": e.folder,
                "is_sent": e.is_sent,
                "body_preview": e.body_text[:200] if e.body_text else "",
            }
            for e in emails[: request.limit]
        ],
    }


@router.get("/sent")
async def get_sent_emails(limit: int = 100):
    """Get recent sent emails."""
    service = EmailIngestionService()
    emails = service.get_sent_emails(limit=limit)

    return {
        "count": len(emails),
        "emails": [
            {
                "id": e.id,
                "subject": e.subject,
                "sender": e.sender,
                "recipients": e.recipients,
                "date": e.date.isoformat(),
                "folder": e.folder,
            }
            for e in emails
        ],
    }


@router.get("/stats")
async def get_email_stats():
    """Get email statistics."""
    service = EmailIngestionService()
    return service.get_stats()


@router.get("/{email_id}")
async def get_email(email_id: str):
    """Get email by ID."""
    service = EmailIngestionService()

    # Search for email
    emails = await service.search_emails(query=email_id)

    for email in emails:
        if email.id == email_id:
            return {
                "id": email.id,
                "subject": email.subject,
                "sender": email.sender,
                "recipients": email.recipients,
                "date": email.date.isoformat(),
                "body_text": email.body_text,
                "body_html": email.body_html,
                "folder": email.folder,
                "is_sent": email.is_sent,
                "labels": email.labels,
            }

    raise HTTPException(status_code=404, detail="Email not found")
