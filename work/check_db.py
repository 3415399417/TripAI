"""Inspect production trip states (temporary script)."""

import io

import psycopg

URL = (
    "postgresql://postgres.cbeprurtzuabemmrvcvs:Tripai123456.."
    "@aws-0-ca-central-1.pooler.supabase.com:6543/postgres"
)
out = io.StringIO()

conn = psycopg.connect(URL, connect_timeout=30)
cur = conn.cursor()
cur.execute(
    "SELECT id, user_id, title, destination, status, created_at "
    "FROM trips ORDER BY id DESC LIMIT 8"
)
rows = cur.fetchall()
for r in rows:
    out.write(f"id={r[0]} user={r[1]} | {r[2]} | {r[3]} | status={r[4]} | {r[5]}\n")
cur.execute("SELECT id, email, nickname FROM users ORDER BY id DESC LIMIT 5")
for r in cur.fetchall():
    out.write(f"user id={r[0]} | {r[1]} | {r[2]}\n")
conn.close()

open(r"E:\TripAI\work\check_db_result.txt", "w", encoding="utf-8").write(out.getvalue())
print("done")
