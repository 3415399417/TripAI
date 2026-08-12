"""SSE streaming endpoint returns stages then a result."""


def test_generate_trip_stream_emits_stages(client, token_factory):
    token = token_factory("stream@tripai.cn")
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "destination": "成都",
        "start_date": "2026-08-20",
        "end_date": "2026-08-20",
        "travelers": 1,
        "budget": 1500,
        "pace": "适中",
        "interests": ["美食"],
    }
    with client.stream(
        "POST", "/api/ai/generate-trip-stream", json=payload, headers=headers
    ) as resp:
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("text/event-stream")
        body = resp.read().decode("utf-8")

    assert "event: stage" in body
    assert "event: result" in body
    assert '"stage": "llm"' in body
