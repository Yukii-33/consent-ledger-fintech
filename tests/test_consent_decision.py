from decimal import Decimal

import pytest

from consent_ledger.consent_service import ConsentLedger


class RecordingCaptcha:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    def verify(self, widget_record_id: str, token: str, ip: str | None, action: str) -> dict[str, object]:
        self.calls.append((widget_record_id, action))
        return {"verified": True}


def test_revocation_blocks_the_next_payment() -> None:
    ledger = ConsentLedger()
    captcha = RecordingCaptcha()
    ledger.grant("user_42", "payments:write", "grant_001")
    ledger.revoke("user_42", "payments:write", "revoke_001")

    with pytest.raises(PermissionError, match="consent is required"):
        ledger.record_payment(
            user_id="user_42",
            amount=Decimal("12.00"),
            event_id="pay_001",
            captcha_widget_record_id=None,
            captcha_token=None,
            ip=None,
            captcha=captcha,
        )

    assert captcha.calls == []
    assert [notice.kind for notice in ledger.notices] == ["consent.granted", "consent.revoked"]


def test_high_risk_payment_verifies_captcha_once() -> None:
    ledger = ConsentLedger()
    captcha = RecordingCaptcha()
    ledger.grant("user_42", "payments:write", "grant_001")

    notice = ledger.record_payment(
        user_id="user_42",
        amount=Decimal("1250.00"),
        event_id="pay_002",
        captcha_widget_record_id="widget_001",
        captcha_token="browser-proof",
        ip="203.0.113.10",
        captcha=captcha,
    )

    assert notice.kind == "payment.accepted"
    assert captcha.calls == [("widget_001", "payment_authorization")]


def test_failed_captcha_blocks_high_risk_payment() -> None:
    ledger = ConsentLedger()
    ledger.grant("user_42", "payments:write", "grant_001")

    class RejectedCaptcha:
        def verify(self, widget_record_id: str, token: str, ip: str | None, action: str) -> dict[str, object]:
            return {"verified": False}

    with pytest.raises(PermissionError, match="captcha verification failed"):
        ledger.record_payment(
            user_id="user_42",
            amount=Decimal("1250.00"),
            event_id="pay_rejected",
            captcha_widget_record_id="widget_001",
            captcha_token="browser-proof",
            ip="203.0.113.10",
            captcha=RejectedCaptcha(),
        )

    assert "pay_rejected" not in ledger._payments
