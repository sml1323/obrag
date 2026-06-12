import os

from sqlmodel import create_engine, SQLModel

# Import all models so SQLModel.metadata knows about them
from core.domain.project import Project  # noqa: F401
from core.domain.chat import Topic, Session, Message  # noqa: F401
from core.domain.settings import Settings  # noqa: F401

sqlite_file_name = os.getenv("DATABASE_PATH", "database.db")
sqlite_url = f"sqlite:///{sqlite_file_name}"

# check_same_thread=False: sync 라우트 핸들러와 스트리밍 응답(iterate_in_threadpool)이
# 서로 다른 스레드풀 스레드에서 동일 커넥션을 (순차적으로) 사용할 수 있으므로 필요.
# 각 요청은 독립 Session을 쓰고 커넥션을 동시 공유하지 않으므로 안전하다.
engine = create_engine(
    sqlite_url,
    echo=False,
    connect_args={"check_same_thread": False},
)


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
