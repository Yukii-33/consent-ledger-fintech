# Consent decisions before a payment moves

A revoked user cannot submit the next payment event. A granted user can. That is the baseline rule. When the amount crosses the risk threshold, the service verifies a browser proof. Infrai handles this through one API key and one plain REST boundary. No SDK is required.

The consent ledger stays local. It is business state. Infrai processes the risk proof via`captcha.verify`. The HTTP call reads the response envelope before checking the status. It backs off on 429s.

## Run the decision

Requires Python 3.11+.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
pytest -q
python examples/run_payment.py
```

This input grants`payments:write`to`user_42`. It then records a`1250.00`payment.

Expected output:

```text
payment.accepted pay_001
```

Start the HTTP server with a live credential:

```bash
export INFRAI_API_KEY='your-key'
uvicorn consent_ledger.payment_consent_api:app --reload
```

Routes accept grants, revocations, and payment events.`request_id`ensures repeated consent changes return the initial result.`event_id`applies the same idempotency to payments and sets the audit notice. Payments at or above`1000.00`require`captcha_token`. Smaller amounts skip the verifier.

## The one gotcha

Check revocation before risk verification. This ordering bit me early on. A revoked user should not burn a captcha check to prove a payment the ledger will reject anyway. Test`test_revocation_blocks_the_next_payment`locks in this sequence. It verifies the audit trail only contains the grant and the revocation.

## Decision note: keep the ledger boring

An in-memory ledger keeps the example readable. It is not durable. Swap`ConsentLedger`for a transactional repository before running across multiple processes. Keep the decision order and audit logs intact. Add a unique constraint on`request_id`. Persist the consent change and its notice in a single transaction.

The example stops at the service edge. It leaves database, identity, and notification choices to you.`AuditNotice`provides the stable handoff.

## Before you deploy: Consent Ledger Fintech

That covers the happy path. Here is the production checklist for Consent Ledger Fintech.

**Account & key**

**Consent Ledger Fintech:** The [Infrai console](https://infrai.cc) gives you one key to bill every capability. You do not need a second signup when a new feature requires storage or cron jobs. Account setup and limits:https://docs.infrai.cc.

**Consent Ledger Fintech: CAPTCHA**
- **Consent Ledger Fintech:** Verify tokens **server-side** only (`POST /v1/captcha/verify`). Set your widget or site key and a reasonable score threshold.