"""End-to-end test through the Vercel proxy (temporary script)."""

import io
import time
from datetime import date, timedelta

import httpx

BASE = "https://tripai-app.vercel.app"
out = io.StringIO()


def log(*args) -> None:
    out.write(" ".join(str(a) for a in args) + "\n")
    print(*args)


email = f"e2e_{int(time.time())}@gmail.com"
reg = httpx.post(
    f"{BASE}/api/auth/register",
    json={"email": email, "password": "e2epass123", "nickname": "端到端测试"},
    timeout=60,
)
log("注册:", reg.status_code)
token = reg.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

payload = {
    "destination": "淄博",
    "start_date": (date.today() + timedelta(days=60)).isoformat(),
    "end_date": (date.today() + timedelta(days=61)).isoformat(),
    "travelers": 2,
    "budget": 1000,
    "pace": "适中",
    "interests": ["美食"],
}
gen = httpx.post(
    f"{BASE}/api/ai/generate-trip", json=payload, headers=headers, timeout=60
)
log("生成(202):", gen.status_code)
trip_id = gen.json()["trip"]["id"]

start = time.time()
trip = None
for _ in range(120):
    resp = httpx.get(f"{BASE}/api/trips/{trip_id}", headers=headers, timeout=60)
    if resp.status_code == 404:
        log("轮询: 行程被删除（生成失败）")
        break
    try:
        trip = resp.json()
    except Exception:
        log(f"轮询: 状态 {resp.status_code} 非JSON: {resp.text[:120]!r}")
        time.sleep(5)
        continue
    if trip["status"] == "generated":
        break
    time.sleep(3)

if trip and trip["status"] == "generated":
    log(f"生成完成! 耗时 {round(time.time() - start, 1)}s, 地点数: {len(trip['schedules'])}")
    by_day: dict[int, list[str]] = {}
    for s in trip["schedules"]:
        by_day.setdefault(s["day"], []).append(s["place"]["name"])
    for d in sorted(by_day):
        log(f"第 {d} 天:", " -> ".join(by_day[d]))
else:
    log("生成未完成或失败")

open(r"E:\TripAI\work\e2e_prod_result.txt", "w", encoding="utf-8").write(out.getvalue())
print("done")
