from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any


class ConsentStatus(StrEnum):
    GRANTED = "granted"
    REVOKED = "revoked"


@dataclass(frozen=True)
class ConsentRecord:
    user_id: str
    scope: str
    status: ConsentStatus
    changed_at: datetime


@dataclass(frozen=True)
class AuditNotice:
    event_id: str
    user_id: str
    kind: str
    summary: str
    occurred_at: datetime


@dataclass
class ConsentLedger:
    high_risk_amount: Decimal = Decimal("1000.00")
    _consents: dict[tuple[str, str], ConsentRecord] = field(default_factory=dict)
    _results: dict[str, ConsentRecord] = field(default_factory=dict)
    _payments: dict[str, AuditNotice] = field(default_factory=dict)
    notices: list[AuditNotice] = field(default_factory=list)

    def grant(self, user_id: str, scope: str, request_id: str) -> ConsentRecord:
        return self._change(user_id, scope, request_id, ConsentStatus.GRANTED)

    def revoke(self, user_id: str, scope: str, request_id: str) -> ConsentRecord:
        return self._change(user_id, scope, request_id, ConsentStatus.REVOKED)

    def record_payment(
        self,
        *,
        user_id: str,
        amount: Decimal,
        event_id: str,
        captcha_widget_record_id: str | None,
        captcha_token: str | None,
        ip: str | None,
        captcha: Any,
    ) -> AuditNotice:
        if event_id in self._payments:
            return self._payments[event_id]
        consent = self._consents.get((user_id, "payments:write"))
        if consent is None or consent.status is not ConsentStatus.GRANTED:
            raise PermissionError("payments:write consent is required")
        if amount >= self.high_risk_amount:
            if not captcha_widget_record_id:
                raise PermissionError("captcha_widget_record_id is required for a high-risk payment")
            if not captcha_token:
                raise PermissionError("captcha_token is required for a high-risk payment")
            result = captcha.verify(captcha_widget_record_id, captcha_token, ip, "payment_authorization")
            if result.get("verified") is not True:
                raise PermissionError("captcha verification failed")
        notice = AuditNotice(
            event_id=event_id,
            user_id=user_id,
            kind="payment.accepted",
            summary=f"Accepted payment event for {amount:.2f}",
            occurred_at=datetime.now(UTC),
        )
        self._payments[event_id] = notice
        self.notices.append(notice)
        return notice

    def _change(self, user_id: str, scope: str, request_id: str, status: ConsentStatus) -> ConsentRecord:
        if request_id in self._results:
            return self._results[request_id]
        record = ConsentRecord(user_id, scope, status, datetime.now(UTC))
        self._consents[(user_id, scope)] = record
        self._results[request_id] = record
        self.notices.append(
            AuditNotice(request_id, user_id, f"consent.{status}", f"{scope} is now {status}", record.changed_at)
        )
        return record
