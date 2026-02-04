from sqlmodel import create_engine, SQLModel

# Import all models so SQLModel.metadata knows about them
from core.domain.project import Project  # noqa: F401
from core.domain.chat import Topic, Session, Message  # noqa: F401
from core.domain.settings import Settings  # noqa: F401

sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

engine = create_engine(sqlite_url, echo=False)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
    _ensure_settings_columns()


def _ensure_settings_columns() -> None:
    """Ensure new Settings columns exist in existing SQLite DB."""
    with engine.connect() as conn:
        result = conn.exec_driver_sql("PRAGMA table_info(settings)")
        existing = {row[1] for row in result}
        if "para_root_path" not in existing:
            conn.exec_driver_sql("ALTER TABLE settings ADD COLUMN para_root_path TEXT")
