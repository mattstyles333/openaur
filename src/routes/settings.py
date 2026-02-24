"""Settings routes - Manage application configuration.

Provides endpoints for persisting and retrieving user settings.
"""

from typing import Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.models.database import get_db, Setting
from datetime import datetime

router = APIRouter()


class SettingUpdate(BaseModel):
    key: str
    value: Any


class SettingsBatchUpdate(BaseModel):
    settings: Dict[str, Any]


@router.get("/")
async def get_all_settings() -> Dict[str, Any]:
    """Get all application settings."""
    try:
        db = next(get_db())
        settings = db.query(Setting).all()
        return {s.key: s.value for s in settings}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{key}")
async def get_setting(key: str) -> Dict[str, Any]:
    """Get a specific setting by key."""
    try:
        db = next(get_db())
        setting = db.query(Setting).filter(Setting.key == key).first()
        if not setting:
            raise HTTPException(status_code=404, detail=f"Setting '{key}' not found")
        return {"key": setting.key, "value": setting.value}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/")
async def update_setting(update: SettingUpdate) -> Dict[str, Any]:
    """Update or create a setting."""
    try:
        db = next(get_db())
        setting = db.query(Setting).filter(Setting.key == update.key).first()

        if setting:
            setting.value = update.value
            setting.updated_at = datetime.utcnow()
        else:
            setting = Setting(key=update.key, value=update.value)
            db.add(setting)

        db.commit()
        return {"success": True, "key": update.key, "value": update.value}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch")
async def update_settings_batch(batch: SettingsBatchUpdate) -> Dict[str, Any]:
    """Update multiple settings at once."""
    try:
        db = next(get_db())
        updated = []

        for key, value in batch.settings.items():
            setting = db.query(Setting).filter(Setting.key == key).first()
            if setting:
                setting.value = value
                setting.updated_at = datetime.utcnow()
            else:
                setting = Setting(key=key, value=value)
                db.add(setting)
            updated.append(key)

        db.commit()
        return {"success": True, "updated": updated, "count": len(updated)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{key}")
async def delete_setting(key: str) -> Dict[str, Any]:
    """Delete a setting."""
    try:
        db = next(get_db())
        setting = db.query(Setting).filter(Setting.key == key).first()
        if not setting:
            raise HTTPException(status_code=404, detail=f"Setting '{key}' not found")

        db.delete(setting)
        db.commit()
        return {"success": True, "message": f"Setting '{key}' deleted"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
