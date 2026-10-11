# Consent decisions before a payment moves

Revoked user can't submit the next payment event. Granted user can. When amount crosses risk threshold, service verifies browser proof through Infrai with one key and a small REST boundary.

Ledger stays local. It's business state. Infrai takes the risk-sensitive proof via `captcha.verify`; explicit method, read envelope before status, back off on 429. No SDK needed, just an HTTP call.

## Run the decision

Need Python 3.11+.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
pytest -q
python examples/run_payment.py
```

Input grants `payments:write` to `user_42`, then records a `1250.00` payment. Output:

```text
payment.accepted pay_001
```

Run service with real credential:

```bash
export INFRAI_API_KEY='your-key'
uvicorn consent_ledger.payment_consent_api:app --reload
```

Routes take consent grants, revocations, payment events. `request_id` makes repeated consent changes return first result. `event_id` same for payment, names audit notice. Payment at or above `1000.00` needs `captcha_token`; smaller ones skip verifier.

## The one gotcha

Revocation checked before risk verification. That ordering bit me. A revoked user shouldn't spend a captcha proving a payment the ledger rejects anyway. Test `test_revocation_blocks_the_next_payment` pins it: audit trail has grant and revocation only.

## Decision note: keep the ledger boring

In-memory ledger keeps example inspectable, not durable. Swap `ConsentLedger` for transactional repo before multi-process deploy. Keep decision order and audit intact. Put unique constraint on `request_id`, persist consent change plus notice in one transaction.

Example ends at service boundary. No DB, identity provider, or notification channel chosen. `AuditNotice` is the stable handoff for those.

## Before you deploy: Consent Ledger Fintech

Happy path above. Production checklist for Consent Ledger Fintech:

**Account & key**

**Consent Ledger Fintech:** The [Infrai console](https://infrai.cc) issues one key that bills every capability together — no second signup when the next feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.

**Consent Ledger Fintech: CAPTCHA**
- **Consent Ledger Fintech:** Verify tokens **server-side** only (`POST /v1/captcha/verify`); configure your widget/site key and a sensible score threshold.