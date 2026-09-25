import httpx

from consent_ledger.infrai_captcha import InfraiCaptcha


def test_retry_after_is_honored_before_success() -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        assert b'"widget_record_id":"widget_001"' in request.content
        if calls == 1:
            return httpx.Response(429, headers={"Retry-After": "2"}, json={"ok": False, "error": {"code": "RATE_LIMITED"}})
        return httpx.Response(200, json={"ok": True, "data": {"verified": True}, "error": None, "metadata": {}})

    delays: list[float] = []
    client = InfraiCaptcha(api_key="test-key", transport=httpx.MockTransport(handler), sleep=delays.append)

    assert client.verify("widget_001", "proof", "203.0.113.10", "payment_authorization") == {"verified": True}
    assert calls == 2
    assert delays == [2.0]
