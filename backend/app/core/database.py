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
    poolclass=NullPool
    if settings.sqlalchemy_database_url.startswith(("postgresql", "mysql"))
    else None,
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
    _seed_prompt_version()


def _seed_prompt_version() -> None:
    """Snapshot the current SYSTEM_PROMPT into prompt_versions once per hash."""
    try:
        import hashlib
        import time

        from app.models.prompt_version import PromptVersion
        from app.services.ai_service import SYSTEM_PROMPT

        prompt_hash = hashlib.sha256(SYSTEM_PROMPT.encode("utf-8")).hexdigest()[:16]
        with SessionLocal() as db:
            exists = (
                db.query(PromptVersion)
                .filter(PromptVersion.prompt_hash == prompt_hash)
                .first()
            )
            if exists:
                return
            count = db.query(PromptVersion).count()
            db.add(
                PromptVersion(
                    version=f"v{count + 1}",
                    prompt_hash=prompt_hash,
                    prompt_text=SYSTEM_PROMPT,
                )
            )
            db.commit()
    except Exception:
        # 版本建档失败不影响主流程
        pass


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
            "alternatives": "TEXT",
            "travel_style": "VARCHAR(32)",
            "city_level": "VARCHAR(32)",
            "city_factor": "FLOAT",
            "daily_budget": "FLOAT",
            "traveler_group": "VARCHAR(16)",
            "weather": "VARCHAR(64)",
            "score_total": "INTEGER",
            "score_detail": "TEXT",
            "llm_seconds": "FLOAT",
        }
        with engine.begin() as conn:
            for column, ddl in wanted.items():
                if column not in existing:
                    conn.execute(text(f"ALTER TABLE trips ADD COLUMN {column} {ddl}"))
        if "places" in inspector.get_table_names():
            place_columns = {column["name"] for column in inspector.get_columns("places")}
            if "cost" not in place_columns:
                with engine.begin() as conn:
                    conn.execute(text("ALTER TABLE places ADD COLUMN cost FLOAT"))
            with engine.begin() as conn:
                for column, ddl in {
                    "opening_hours": "VARCHAR(512)",
                    "phone": "VARCHAR(64)",
                    "photos": "TEXT",
                }.items():
                    if column not in place_columns:
                        conn.execute(
                            text(f"ALTER TABLE places ADD COLUMN {column} {ddl}")
                        )
    except Exception:
        # Failures here are non-fatal; app code tolerates missing attributes.
        pass
