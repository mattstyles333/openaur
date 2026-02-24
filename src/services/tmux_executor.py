import os
import subprocess
import uuid
from datetime import datetime


class TmuxExecutor:
    """Tmux session manager for async command execution."""

    def __init__(self):
        self.sessions = {}

    def create_session(
        self,
        action_id: str,
        command: str,
        async_exec: bool = True,
        cwd: str | None = None,
        env: dict | None = None,
    ) -> dict:
        """Create a new tmux session for command execution."""

        # Generate unique IDs
        session_id = str(uuid.uuid4())[:8]
        tmux_session = f"openaur-{action_id}-{session_id}"

        # Ensure session name is valid (no dots)
        tmux_session = tmux_session.replace(".", "-")

        try:
            # Create tmux session
            create_cmd = ["tmux", "new-session", "-d", "-s", tmux_session]

            subprocess.run(create_cmd, check=True, capture_output=True)

            # Prepare command with monitoring
            wrapped_cmd = self._wrap_command(command, session_id)

            # Execute command in tmux session
            exec_cmd = ["tmux", "send-keys", "-t", tmux_session, wrapped_cmd, "Enter"]

            subprocess.run(exec_cmd, check=True, capture_output=True)

            # Store session info
            session_info = {
                "id": session_id,
                "tmux_session": tmux_session,
                "action_id": action_id,
                "command": command,
                "cwd": cwd or os.getcwd(),
                "env": env or {},
                "status": "running",
                "started_at": datetime.utcnow().isoformat(),
            }

            self.sessions[session_id] = session_info

            return session_info

        except subprocess.CalledProcessError as e:
            raise Exception(
                f"Failed to create tmux session: {e.stderr.decode() if e.stderr else str(e)}"
            )
        except Exception as e:
            raise Exception(f"Unexpected error: {str(e)}")

    def _wrap_command(self, command: str, session_id: str) -> str:
        """Wrap command with status tracking."""
        # Write exit code to file on completion
        status_file = f"/tmp/openaur-{session_id}.status"

        wrapped = f"""
{command}
EXIT_CODE=$?
echo $EXIT_CODE > {status_file}
exit $EXIT_CODE
""".strip()

        return wrapped

    def get_session_status(self, tmux_session: str) -> dict:
        """Get session status and exit code."""
        try:
            # Check if session exists
            result = subprocess.run(
                ["tmux", "has-session", "-t", tmux_session], capture_output=True
            )

            if result.returncode != 0:
                # Session doesn't exist, check if completed
                session_id = tmux_session.split("-")[-1]
                status_file = f"/tmp/openaur-{session_id}.status"

                if os.path.exists(status_file):
                    with open(status_file) as f:
                        exit_code = int(f.read().strip())

                    return {
                        "status": "completed" if exit_code == 0 else "failed",
                        "exit_code": exit_code,
                        "tmux_session": tmux_session,
                    }

                return {
                    "status": "unknown",
                    "exit_code": None,
                    "tmux_session": tmux_session,
                }

            # Session still running
            return {
                "status": "running",
                "exit_code": None,
                "tmux_session": tmux_session,
            }

        except Exception as e:
            return {"status": "error", "error": str(e), "tmux_session": tmux_session}

    def get_session_output(self, session_id: str, lines: int = 50) -> str:
        """Get session output."""
        try:
            # Find session by ID
            session_info = self.sessions.get(session_id)
            if not session_info:
                return "Session not found"

            tmux_session = session_info["tmux_session"]

            # Capture output
            result = subprocess.run(
                ["tmux", "capture-pane", "-t", tmux_session, "-p", "-S", f"-{lines}"],
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                return result.stdout
            else:
                return f"Failed to get output: {result.stderr}"

        except Exception as e:
            return f"Error: {str(e)}"

    def list_sessions(self) -> list[dict]:
        """List all active tmux sessions."""
        try:
            result = subprocess.run(
                ["tmux", "list-sessions", "-F", "#{session_name}|#{session_created}"],
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                return []

            sessions = []
            for line in result.stdout.strip().split("\n"):
                if "|" in line:
                    name, created = line.split("|")
                    if name.startswith("openaur-"):
                        sessions.append({"name": name, "created": created})

            return sessions

        except Exception as e:
            print(f"Error listing sessions: {e}")
            return []

    def kill_session(self, tmux_session: str) -> bool:
        """Kill a tmux session."""
        try:
            subprocess.run(
                ["tmux", "kill-session", "-t", tmux_session],
                check=True,
                capture_output=True,
            )
            return True
        except:
            return False
