from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import NullPool

from app.core.config import get_settings

settings = get_settings()

connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.sqlalchemy_database_url,
    connect_args=connect_args,
    pool_pre_ping=True,
    # Supabase 事务模式连接池不支持持久连接，用 NullPool 最稳妥
    poolclass=NullPool if settings.sqlalchemy_database_url.startswith("postgresql") else None,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    """FastAPI dependency that yields a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create all tables. Import models first so metadata is populated."""
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _apply_light_migrations()


def _apply_light_migrations() -> None:
    """Add newly introduced columns to an existing `trips` table.

    `create_all` does not alter existing tables, so new columns are added
    explicitly after inspecting the current columns.
    """
    try:
        inspector = inspect(engine)
        if "trips" not in inspector.get_table_names():
            return
        existing = {column["name"] for column in inspector.get_columns("trips")}
        wanted = {
            "traveler_profile": "VARCHAR(255)",
            "consumption_level": "VARCHAR(32)",
            "budget_min": "FLOAT",
            "budget_max": "FLOAT",
            "budget_breakdown": "TEXT",
        }
        with engine.begin() as conn:
            for column, ddl in wanted.items():
                if column not in existing:
                    conn.execute(text(f"ALTER TABLE trips ADD COLUMN {column} {ddl}"))
    except Exception:
        # Failures here are non-fatal; app code tolerates missing attributes.
        pass
