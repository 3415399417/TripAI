r"""One-off migration: Supabase PostgreSQL -> Aliyun RDS MySQL.

Reads every row from the source (Supabase) and inserts it into the target
(RDS MySQL) preserving primary keys and relationships. Run from backend/:

    $env:SUPABASE_DATABASE_URL="postgresql://..."
    $env:MYSQL_DATABASE_URL="mysql+pymysql://user:pass@host:3306/tripai?charset=utf8mb4"
    .venv\Scripts\python.exe scripts\migrate_supabase_to_mysql.py
"""

from __future__ import annotations

import os
import sys

from sqlalchemy import create_engine, inspect, text

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main() -> None:
    src_url = os.environ.get("SUPABASE_DATABASE_URL")
    dst_url = os.environ.get("MYSQL_DATABASE_URL")
    if not src_url or not dst_url:
        print("SUPABASE_DATABASE_URL and MYSQL_DATABASE_URL are required")
        sys.exit(1)

    src = create_engine(
        src_url.replace("postgresql://", "postgresql+psycopg://", 1),
        pool_pre_ping=True,
    )

    # Ensure target database exists (connect without db name first).
    base_url, _, query = dst_url.partition("?")
    db_name = base_url.rsplit("/", 1)[-1]
    server_url = base_url.rsplit("/", 1)[0] + "/mysql"
    if query:
        server_url += "?" + query
    server = create_engine(server_url, pool_pre_ping=True)
    with server.connect() as conn:
        conn.execute(
            text(
                f"CREATE DATABASE IF NOT EXISTS `{db_name}` "
                "DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
        )
        conn.commit()
    server.dispose()

    dst = create_engine(dst_url, pool_pre_ping=True)
    from app.core.database import Base
    from app import models  # noqa: F401  # registers tables on Base.metadata

    Base.metadata.create_all(bind=dst)
    dst_inspector = inspect(dst)
    for table in ["users", "places", "trips", "schedules"]:
        if table not in dst_inspector.get_table_names():
            print(f"target table {table} missing")
            sys.exit(1)
        count = dst.connect().execute(text(f"SELECT COUNT(*) FROM `{table}`")).scalar()
        if count:
            print(f"target table {table} already has {count} rows; aborting")
            sys.exit(1)

    # Copy rows preserving IDs: parents first, children last.
    tables = ["users", "places", "trips", "schedules"]
    for table in tables:
        src_columns = [
            col["name"] for col in inspect(src).get_columns(table)
        ]
        dst_columns = [
            col["name"] for col in inspect(dst).get_columns(table)
        ]
        columns = [c for c in src_columns if c in dst_columns]
        if not columns:
            print(f"no common columns for {table}; aborting")
            sys.exit(1)
        col_sql = ", ".join(columns)
        col_sql_dst = ", ".join(f"`{c}`" for c in columns)
        placeholders = ", ".join(":" + c for c in columns)
        with src.connect() as sconn:
            rows = sconn.execute(text(f"SELECT {col_sql} FROM {table}")).mappings().all()
        with dst.begin() as dconn:
            for row in rows:
                params = {c: row[c] for c in columns}
                dconn.execute(
                    text(
                        f"INSERT INTO `{table}` ({col_sql_dst}) VALUES ({placeholders})"
                    ),
                    params,
                )
        print(f"{table}: copied {len(rows)} rows")

    print("MIGRATION DONE")


if __name__ == "__main__":
    main()
