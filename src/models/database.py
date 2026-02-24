from sqlalchemy import (
    create_engine,
    Column,
    String,
    Integer,
    Boolean,
    DateTime,
    Text,
    ForeignKey,
    JSON,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

# Create data directory before engine initialization
data_dir = "/home/aura/app/data"
os.makedirs(data_dir, exist_ok=True)

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{data_dir}/openaura.db")

Base = declarative_base()
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class InstalledPackage(Base):
    __tablename__ = "installed_packages"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    source = Column(String)
    version = Column(String)
    installed_at = Column(DateTime, default=datetime.utcnow)
    last_used = Column(DateTime)
    auto_installed = Column(Boolean, default=False)
    requested_by = Column(String)


class PackageCleanupQueue(Base):
    __tablename__ = "package_cleanup_queue"

    id = Column(Integer, primary_key=True, index=True)
    package_name = Column(String, ForeignKey("installed_packages.name"))
    installed_at = Column(DateTime)
    last_used = Column(DateTime)
    cleanup_scheduled_at = Column(DateTime)


class ActionRegistry(Base):
    __tablename__ = "action_registry"

    id = Column(String, primary_key=True)
    binary_path = Column(String, unique=True, nullable=False)
    yaml_path = Column(String)
    safety_level = Column(Integer)
    description = Column(Text)
    indexed_at = Column(DateTime, default=datetime.utcnow)
    last_used = Column(DateTime)


class Session(Base):
    __tablename__ = "sessions"

    id = Column(String, primary_key=True)
    tmux_session = Column(String, unique=True)
    action_id = Column(String, ForeignKey("action_registry.id"))
    command = Column(Text)
    cwd = Column(String)
    env = Column(JSON)
    status = Column(String)
    exit_code = Column(Integer)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)


class ExecutionContext(Base):
    __tablename__ = "execution_contexts"

    id = Column(String, primary_key=True)
    session_id = Column(String, ForeignKey("sessions.id"))
    system_prompt = Column(Text)
    tools_injected = Column(JSON)
    user_query = Column(Text)
    emotional_state = Column(JSON)
    timestamp = Column(DateTime, default=datetime.utcnow)


class EmailSyncState(Base):
    __tablename__ = "email_sync_state"

    id = Column(Integer, primary_key=True)
    provider = Column(String)
    last_sync_timestamp = Column(DateTime)
    last_message_id = Column(String)
    retention_days = Column(Integer, default=90)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def init_db():
    """Initialize database tables."""
    # Data directory is already created at module import time
    Base.metadata.create_all(bind=engine)
    print("✓ Database initialized")
