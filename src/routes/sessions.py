
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.models.database import Session as SessionModel
from src.models.database import get_db
from src.models.schemas import SessionCreateRequest, SessionResponse
from src.services.tmux_executor import TmuxExecutor

router = APIRouter()
tmux_executor = TmuxExecutor()


@router.post("/create", response_model=SessionResponse)
async def create_session(request: SessionCreateRequest, db: Session = Depends(get_db)):
    """Create a new tmux session for command execution."""
    try:
        session = tmux_executor.create_session(
            action_id=request.action_id,
            command=request.command,
            async_exec=request.async_exec,
        )

        # Save to database
        db_session = SessionModel(
            id=session["id"],
            tmux_session=session["tmux_session"],
            action_id=request.action_id,
            command=request.command,
            status="running",
        )
        db.add(db_session)
        db.commit()

        return SessionResponse(
            id=session["id"],
            tmux_session=session["tmux_session"],
            status="running",
            command=request.command,
            started_at=db_session.started_at,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str, db: Session = Depends(get_db)):
    """Get session status."""
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Check tmux status
    status = tmux_executor.get_session_status(session.tmux_session)

    return SessionResponse(
        id=session.id,
        tmux_session=session.tmux_session,
        status=status.get("status", session.status),
        command=session.command,
        started_at=session.started_at,
        completed_at=session.completed_at,
        exit_code=status.get("exit_code") or session.exit_code,
    )


@router.get("/{session_id}/output")
async def get_session_output(session_id: str, lines: int = 50):
    """Get session output."""
    try:
        output = tmux_executor.get_session_output(session_id, lines=lines)
        return {"output": output}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def list_sessions(db: Session = Depends(get_db)):
    """List all active sessions."""
    sessions = db.query(SessionModel).filter(SessionModel.status == "running").all()
    return [
        {
            "id": s.id,
            "tmux_session": s.tmux_session,
            "status": s.status,
            "command": s.command,
            "started_at": s.started_at,
        }
        for s in sessions
    ]


@router.post("/{session_id}/kill")
async def kill_session(session_id: str, db: Session = Depends(get_db)):
    """Kill an active session."""
    try:
        session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # Kill the tmux session
        import subprocess
        subprocess.run(
            ["tmux", "kill-session", "-t", session.tmux_session],
            capture_output=True
        )

        # Update database
        session.status = "killed"
        db.commit()

        return {"success": True, "message": f"Session {session_id} killed"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
