"""Email ingestion service for openaur.

Syncs emails from providers using offlineimap or gogcli.
Stores emails for RAG and memory indexing.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from pathlib import Path
import re
import json


@dataclass
class Email:
    """Represents an email message."""

    id: str
    subject: str
    sender: str
    recipients: List[str]
    date: datetime
    body_text: str
    body_html: Optional[str] = None
    folder: str = "INBOX"
    is_sent: bool = False
    thread_id: Optional[str] = None
    labels: List[str] = None
    attachments: List[Dict[str, Any]] = None

    def __post_init__(self):
        if self.labels is None:
            self.labels = []
        if self.attachments is None:
            self.attachments = []


class EmailIngestionService:
    """Service for ingesting emails from various providers.

    Supports:
    - Gmail via Gogcli (Google Takeout)
    - IMAP via OfflineIMAP
    - Local mbox files
    """

    def __init__(self, storage_path: str = "/home/aura/app/data/emails"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # Sent folder patterns
        self.sent_folders = [
            "[Gmail]/Sent Mail",
            "[Gmail]/Gesendet",
            "Sent",
            "Sent Items",
            "Gesendet",
            "已发送邮件",
        ]

    async def sync_gogcli(self, takeout_path: str) -> Dict[str, Any]:
        """Sync emails from Google Takeout (Gogcli format).

        Args:
            takeout_path: Path to extracted Takeout/Mail directory

        Returns:
            Sync statistics
        """
        takeout_dir = Path(takeout_path)
        if not takeout_dir.exists():
            return {"error": f"Takeout path not found: {takeout_path}"}

        emails_processed = 0
        errors = []

        # Process mbox files
        for mbox_file in takeout_dir.rglob("*.mbox"):
            try:
                folder_name = mbox_file.parent.name
                is_sent = any(
                    pattern.lower() in folder_name.lower()
                    for pattern in self.sent_folders
                )

                emails = self._parse_mbox(mbox_file, folder_name, is_sent)

                for email in emails:
                    await self._store_email(email)
                    emails_processed += 1

            except Exception as e:
                errors.append(f"Error processing {mbox_file}: {str(e)}")

        return {
            "provider": "gogcli",
            "emails_processed": emails_processed,
            "errors": errors,
            "synced_at": datetime.utcnow().isoformat(),
        }

    async def sync_offlineimap(self, maildir_path: str) -> Dict[str, Any]:
        """Sync emails from OfflineIMAP Maildir.

        Args:
            maildir_path: Path to Maildir directory

        Returns:
            Sync statistics
        """
        maildir = Path(maildir_path)
        if not maildir.exists():
            return {"error": f"Maildir not found: {maildir_path}"}

        emails_processed = 0

        # Walk Maildir structure
        for folder in maildir.iterdir():
            if folder.is_dir():
                folder_name = folder.name

                # Detect if this is a sent folder
                is_sent = any(
                    pattern.lower() in folder_name.lower()
                    for pattern in self.sent_folders
                )

                # Process cur and new subdirectories
                for subdir in ["cur", "new"]:
                    subdir_path = folder / subdir
                    if subdir_path.exists():
                        for email_file in subdir_path.iterdir():
                            if email_file.is_file():
                                try:
                                    email = self._parse_maildir_file(
                                        email_file, folder_name, is_sent
                                    )
                                    await self._store_email(email)
                                    emails_processed += 1
                                except Exception as e:
                                    print(f"Error parsing {email_file}: {e}")

        return {
            "provider": "offlineimap",
            "emails_processed": emails_processed,
            "synced_at": datetime.utcnow().isoformat(),
        }

    def _parse_mbox(self, mbox_path: Path, folder: str, is_sent: bool) -> List[Email]:
        """Parse an mbox file into Email objects."""
        emails = []
        content = mbox_path.read_text(encoding="utf-8", errors="ignore")

        # Split by From lines
        messages = re.split(r"\nFrom [^\n]+\n", content)

        for i, message in enumerate(messages[1:], 1):  # Skip first empty split
            try:
                email = self._parse_email_content(message, folder, is_sent)
                if email:
                    emails.append(email)
            except Exception as e:
                print(f"Error parsing message {i}: {e}")

        return emails

    def _parse_maildir_file(
        self, email_path: Path, folder: str, is_sent: bool
    ) -> Email:
        """Parse a single Maildir email file."""
        content = email_path.read_text(encoding="utf-8", errors="ignore")
        return self._parse_email_content(content, folder, is_sent)

    def _parse_email_content(
        self, content: str, folder: str, is_sent: bool
    ) -> Optional[Email]:
        """Parse raw email content into Email object."""
        # Simple header parsing
        header_match = re.match(r"((?:[^\n]+\n)+)\n(.*)", content, re.DOTALL)
        if not header_match:
            return None

        headers_text, body = header_match.groups()
        headers = self._parse_headers(headers_text)

        # Extract body parts
        body_text = body
        body_html = None

        # Check for multipart
        if "Content-Type: multipart" in headers_text:
            body_text, body_html = self._parse_multipart(body)

        # Create email ID
        message_id = headers.get("Message-Id", "")
        if not message_id:
            message_id = hash(body[:100])

        email_id = re.sub(r"[^a-zA-Z0-9]", "_", message_id)[:64]

        return Email(
            id=email_id,
            subject=headers.get("Subject", "No Subject"),
            sender=headers.get("From", ""),
            recipients=self._parse_addresses(headers.get("To", "")),
            date=self._parse_date(headers.get("Date", "")),
            body_text=self._clean_body(body_text),
            body_html=body_html,
            folder=folder,
            is_sent=is_sent,
        )

    def _parse_headers(self, headers_text: str) -> Dict[str, str]:
        """Parse email headers."""
        headers = {}
        current_key = None

        for line in headers_text.split("\n"):
            if line.startswith(" ") or line.startswith("\t"):
                # Continuation of previous header
                if current_key:
                    headers[current_key] += " " + line.strip()
            else:
                if ":" in line:
                    key, value = line.split(":", 1)
                    current_key = key.strip()
                    headers[current_key] = value.strip()

        return headers

    def _parse_addresses(self, address_string: str) -> List[str]:
        """Parse email addresses from string."""
        if not address_string:
            return []

        # Simple regex for email extraction
        emails = re.findall(r"[\w\.-]+@[\w\.-]+\.\w+", address_string)
        return emails

    def _parse_date(self, date_string: str) -> datetime:
        """Parse date string to datetime."""
        try:
            # Try common formats
            formats = [
                "%a, %d %b %Y %H:%M:%S %z",
                "%d %b %Y %H:%M:%S %z",
                "%a, %d %b %Y %H:%M:%S",
                "%Y-%m-%d %H:%M:%S",
            ]

            for fmt in formats:
                try:
                    return datetime.strptime(date_string.strip(), fmt)
                except ValueError:
                    continue

            return datetime.utcnow()
        except:
            return datetime.utcnow()

    def _parse_multipart(self, body: str) -> tuple:
        """Parse multipart email body."""
        # Simple multipart parsing
        text_part = body
        html_part = None

        # Look for HTML part
        if "Content-Type: text/html" in body:
            parts = body.split("Content-Type: text/html")
            if len(parts) > 1:
                html_content = parts[1]
                # Extract content after headers
                if "\n\n" in html_content:
                    html_part = html_content.split("\n\n", 1)[1]

                # Look for text part
                if "Content-Type: text/plain" in body:
                    text_parts = body.split("Content-Type: text/plain")
                    if len(text_parts) > 1:
                        text_content = text_parts[1]
                        if "\n\n" in text_content:
                            text_part = text_content.split("\n\n", 1)[1]

        return text_part, html_part

    def _clean_body(self, body: str) -> str:
        """Clean email body text."""
        # Remove quoted printable encoding markers
        body = re.sub(r"=\n", "", body)
        body = re.sub(r"=[0-9A-F]{2}", "", body)

        # Remove excessive whitespace
        body = re.sub(r"\n{3,}", "\n\n", body)

        return body.strip()

    async def _store_email(self, email: Email):
        """Store email to disk and index."""
        # Create storage path based on date
        date_folder = email.date.strftime("%Y/%m")
        email_dir = self.storage_path / date_folder
        email_dir.mkdir(parents=True, exist_ok=True)

        # Save email as JSON
        email_file = email_dir / f"{email.id}.json"

        email_data = {
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
            "thread_id": email.thread_id,
        }

        email_file.write_text(json.dumps(email_data, indent=2))

        # TODO: Index to OpenMemory for RAG

    async def search_emails(
        self,
        query: str,
        folder: Optional[str] = None,
        since: Optional[datetime] = None,
        is_sent: Optional[bool] = None,
    ) -> List[Email]:
        """Search stored emails."""
        results = []

        query_lower = query.lower()

        # Walk storage directory
        for email_file in self.storage_path.rglob("*.json"):
            try:
                data = json.loads(email_file.read_text())

                # Filter by folder
                if folder and data.get("folder") != folder:
                    continue

                # Filter by sent status
                if is_sent is not None and data.get("is_sent") != is_sent:
                    continue

                # Filter by date
                if since:
                    email_date = datetime.fromisoformat(data.get("date", ""))
                    if email_date < since:
                        continue

                # Search in subject and body
                subject = data.get("subject", "").lower()
                body = data.get("body_text", "").lower()

                if query_lower in subject or query_lower in body:
                    results.append(self._dict_to_email(data))

            except Exception as e:
                print(f"Error loading {email_file}: {e}")

        return results

    def _dict_to_email(self, data: Dict) -> Email:
        """Convert dict to Email object."""
        return Email(
            id=data["id"],
            subject=data["subject"],
            sender=data["sender"],
            recipients=data["recipients"],
            date=datetime.fromisoformat(data["date"]),
            body_text=data["body_text"],
            body_html=data.get("body_html"),
            folder=data["folder"],
            is_sent=data["is_sent"],
            labels=data.get("labels", []),
            thread_id=data.get("thread_id"),
        )

    def get_sent_emails(self, limit: int = 100) -> List[Email]:
        """Get recent sent emails."""
        sent = []

        for email_file in sorted(
            self.storage_path.rglob("*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )[:limit]:
            try:
                data = json.loads(email_file.read_text())
                if data.get("is_sent"):
                    sent.append(self._dict_to_email(data))
            except Exception as e:
                print(f"Error loading {email_file}: {e}")

        return sent[:limit]

    def get_stats(self) -> Dict[str, Any]:
        """Get email statistics."""
        total = 0
        sent_count = 0
        by_folder = {}

        for email_file in self.storage_path.rglob("*.json"):
            try:
                data = json.loads(email_file.read_text())
                total += 1

                if data.get("is_sent"):
                    sent_count += 1

                folder = data.get("folder", "unknown")
                by_folder[folder] = by_folder.get(folder, 0) + 1

            except:
                pass

        return {
            "total_emails": total,
            "sent_emails": sent_count,
            "by_folder": by_folder,
            "storage_path": str(self.storage_path),
        }
