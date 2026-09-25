from __future__ import annotations

from decimal import Decimal

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .consent_service import AuditNotice, ConsentLedger, ConsentRecord
from .infrai_captcha import InfraiCaptcha, InfraiError


class ConsentChange(BaseModel):
    user_id: str
    scope: str
    request_id: str


class PaymentEvent(BaseModel):
    user_id: str
    amount: Decimal = Field(gt=0)
    event_id: str
    captcha_widget_record_id: str | None = None
    captcha_token: str | None = None
    ip: str | None = None


ledger = ConsentLedger()
app = FastAPI(title="Payment consent ledger")


@app.post("/consents/grants", response_model=ConsentRecord)
def grant_consent(change: ConsentChange) -> ConsentRecord:
    return ledger.grant(change.user_id, change.scope, change.request_id)


@app.post("/consents/revocations", response_model=ConsentRecord)
def revoke_consent(change: ConsentChange) -> ConsentRecord:
    return ledger.revoke(change.user_id, change.scope, change.request_id)


@app.post("/payment-events", response_model=AuditNotice)
def record_payment(event: PaymentEvent) -> AuditNotice:
    try:
        return ledger.record_payment(
            user_id=event.user_id,
            amount=event.amount,
            event_id=event.event_id,
            captcha_widget_record_id=event.captcha_widget_record_id,
            captcha_token=event.captcha_token,
            ip=event.ip,
            captcha=InfraiCaptcha(),
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except InfraiError as exc:
        status = exc.status_code if 400 <= exc.status_code < 500 else 502
        raise HTTPException(status_code=status, detail={"code": exc.code, "message": str(exc)}) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail="Captcha verification could not be completed") from exc
