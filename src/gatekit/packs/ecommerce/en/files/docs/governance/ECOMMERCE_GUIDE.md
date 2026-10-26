# ECOMMERCE_GUIDE — e-commerce industry rules ({{PROJECT}})

Supplements `GATE_PROTOCOL`. Primary gates: `checkout-lead` (zone T), `pricing-lead` (zone F).

## 1. Suggested risk zones (declare them in `gatekit.toml`)

| Zone | Typical code | Example regex |
|---|---|---|
| T | ordering, payments, webhooks, refunds, stock decrement | `'^src/(orders?|checkout|payments?|refunds?|inventory|webhooks?)/'` |
| K | accounts, sessions, store admin permissions, payment-provider keys | `'^src/(auth|accounts?|admin)/'` |
| F | prices, promotions, coupons, tax, shipping fees | `'^src/(pricing|promotions?|coupons?|tax|shipping)/'` |

## 2. The pack's guards

| Guard | Blocks |
|---|---|
| `money_float` | money typed as float / cast to float / FLOAT·REAL·DOUBLE columns / `parseFloat` of money names |
| `pci_scope` | columns or fields storing card numbers, CVV, magnetic stripe data |

## 3. Hard rules

1. **Exact money:** integer minor units (`amount_minor BIGINT` + `currency CHAR(3)`) or `Decimal` / `NUMERIC(p,s)`.
   Money always travels with its currency.
2. **One place computes prices:** prices, discounts, tax and fees are computed server-side in one module; the UI only displays.
3. **An explicit order state machine**, transitions through one function; an illegal transition ⇒ named refusal.
4. **Idempotency** for every capture and refund; webhooks verify the signature + replay protection + tolerate duplicates/out-of-order.
5. **Totals agree:** sum of lines = order total = charged = booked; total refunded ≤ total captured.
6. **Atomic stock**, time-limited reservations.
7. **PCI:** never store card numbers / CVV; only token + last4 + brand.
8. **Personal data** (addresses, phone numbers): minimal collection, retention limits, never in logs.

## 4. Sample mutant suite (zone T)

```toml
zone = "T"
cmd = "PYTHONPATH=src python -m pytest -q tests/checkout"

[[mutant]]
id = "pay-idem-01"
file = "src/payments/capture.py"
find = "idempotency_key=order.payment_key"
replace = "idempotency_key=None"
why = "drops the idempotency key ⇒ a retry after a network error charges the customer twice"

[[mutant]]
id = "refund-cap-01"
file = "src/refunds/service.py"
find = "if refunded + amount > captured:"
replace = "if False:"
why = "drops the refund ceiling ⇒ refunds more than was captured"

[[mutant]]
id = "webhook-sig-01"
file = "src/webhooks/provider.py"
find = "if not verify_signature(raw_body, header_sig, secret):"
replace = "if False:"
why = "drops the webhook signature check ⇒ anyone can forge a 'paid' event"
```
