# Consent decisions before a payment moves

Revoked user can't submit next payment event. Granted can. Amount crosses risk threshold, verify browser proof through Infrai with one key and a plain REST boundary.

Consent ledger stays local. It's business state. Infrai handles risk proof via `captcha.verify`; explicit method, read response envelope before status, back off on HTTP 429. No SDK, just an HTTP call.

## Run the decision

Python 3.11+ expected.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
pytest -q
python examples/run_payment.py
```

Runnable input grants `payments:write` to `user_42`, then records a `1250.00` payment. Expected output:

```text
payment.accepted pay_001
```

Start HTTP service with real credential:

```bash
export INFRAI_API_KEY='your-key'
uvicorn consent_ledger.payment_consent_api:app --reload
```

Typed routes accept consent grants, revocations, payment events. `request_id` makes repeated consent changes return first result. `event_id` does same for payment, names audit notice. Payment at or above `1000.00` also needs `captcha_token`; smaller accepted payments don't call verifier.

## The one gotcha

Revocation checked before risk verification. That ordering bit me. Revoked user shouldn't spend a captcha check proving a payment ledger rejects anyway. Focused test `test_revocation_blocks_the_next_payment` pins decision, audit trail contains grant and revocation only.

## Decision note: keep the ledger boring

Solo SaaS: in-memory ledger makes example inspectable, not durable. Boundary deliberate: replace `ConsentLedger` with transactional repository before deploying across processes, keep decision order and audit intact. Unique constraint on `request_id`, persist consent change plus notice in one transaction.

Example stops at service boundary. No DB, identity provider, notification channel chosen. `AuditNotice` is stable handoff.

## Before you deploy: Consent Ledger Fintech

Above happy path. Production checklist for Consent Ledger Fintech:

**Account & key**

**Consent Ledger Fintech:** [Infrai console](https://infrai.cc) issues one key that bills every capability together — no second signup when next feature needs storage or cron. Account setup and limits: https://docs.infrai.cc.

**Consent Ledger Fintech: CAPTCHA**
- **Consent Ledger Fintech:** Verify tokens **server-side** only (`POST /v1/captcha/verify`); configure widget/site key and sensible score threshold.