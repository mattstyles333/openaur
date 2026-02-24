from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Optional

from src.models.database import get_db, InstalledPackage
from src.models.schemas import PackageSearchResult, PackageInstallRequest
from src.services.package_manager import PackageManager

router = APIRouter()


@router.get("/search")
async def search_packages(q: str, limit: int = 20):
    """Search for packages using yay."""
    try:
        pm = PackageManager()
        results = pm.search_packages(q, limit)
        return {"packages": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/install")
async def install_package(
    request: PackageInstallRequest, db: Session = Depends(get_db)
):
    """Install a package."""
    try:
        pm = PackageManager()
        result = pm.install_package(request.package)

        if result["success"]:
            # Record in database
            pkg = InstalledPackage(
                name=request.package,
                source=result.get("source", "unknown"),
                auto_installed=request.auto,
                requested_by=request.context or "user",
            )
            db.add(pkg)
            db.commit()

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/installed")
async def list_installed_packages(db: Session = Depends(get_db)):
    """List all installed packages."""
    packages = db.query(InstalledPackage).all()
    return [
        {
            "name": p.name,
            "source": p.source,
            "version": p.version,
            "installed_at": p.installed_at,
            "auto_installed": p.auto_installed,
        }
        for p in packages
    ]


@router.delete("/{package_name}")
async def remove_package(package_name: str, db: Session = Depends(get_db)):
    """Remove a package and schedule cleanup."""
    try:
        pm = PackageManager()
        result = pm.remove_package(package_name)

        # Mark for cleanup in database
        pkg = (
            db.query(InstalledPackage)
            .filter(InstalledPackage.name == package_name)
            .first()
        )
        if pkg:
            # Actually delete or mark as uninstalled
            db.delete(pkg)
            db.commit()

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
