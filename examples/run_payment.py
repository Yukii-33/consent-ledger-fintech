from decimal import Decimal

from consent_ledger.consent_service import ConsentLedger


class AcceptedCaptcha:
    def verify(self, widget_record_id: str, token: str, ip: str | None, action: str) -> dict[str, object]:
        return {"verified": True}


ledger = ConsentLedger()
ledger.grant("user_42", "payments:write", "grant_001")
notice = ledger.record_payment(
    user_id="user_42",
    amount=Decimal("1250.00"),
    event_id="pay_001",
    captcha_widget_record_id="widget_001",
    captcha_token="browser-proof",
    ip="203.0.113.10",
    captcha=AcceptedCaptcha(),
)
print(notice.kind, notice.event_id)
