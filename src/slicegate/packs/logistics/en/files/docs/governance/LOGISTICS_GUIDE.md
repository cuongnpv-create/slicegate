# LOGISTICS_GUIDE — logistics industry rules ({{PROJECT}})

Supplements `GATE_PROTOCOL`. Primary gates: `fulfillment-lead` (bookings, labels, shipment states, zone T),
`routing-lead` (rates, units, ETA, cut-offs, zone F). Pair with `multi_provider` when you integrate several carriers,
with `ecommerce` when you collect cash on delivery.

## 1. Suggested risk zones (declare them in `slicegate.toml`)

| Zone | Typical code | Example regex |
|---|---|---|
| T | carrier booking, labels, pickups, shipment state machine, carrier webhooks, stock reservation, COD | `'^src/(booking|labels?|shipments?|carriers?|webhooks?|inventory|cod)/'` |
| F | rating, dimensional weight, unit conversion, ETA, cut-offs, SLAs, capacity, route optimization | `'^src/(rating|rates?|units|eta|sla|capacity|routing)/'` |
| K | carrier API keys, customer addresses and phone numbers, driver locations | `'^src/(auth|secrets|addresses|tracking/location)/'` |

## 2. The pack's guards

| Guard | Blocks |
|---|---|
| `unit_suffix` | quantity names (weight, distance, length, volume, temperature…) without a unit word (`kg`, `km`, `cbm`, `c`…) — Python, JS/TS, SQL |
| `naive_time` | timestamps without a time zone: `datetime.utcnow()`, `datetime.now()` without tz, `datetime(…)` without `tzinfo`; SQL `timestamp` / `datetime`; JS `new Date("… hh:mm")` without `Z` / offset |

Exemptions, one site at a time with a reason: `units: ignore <reason>`, `naive-time: ignore <reason>`. If your codebase
uses other words (e.g. `gw` for gross weight), extend `[packs.logistics]` instead of exempting.

`length` is not a default quantity word (string / list lengths would drown the signal); parcels are still caught
through `width` / `height` / `depth`. Add it if your code never uses `length` for counts. UI component files
(`.tsx` / `.jsx`) are skipped by default (`unit_skip`): their `width` / `height` are layout pixels.

## 3. Hard rules

1. **Units in names, conversions in one module**, exact constants, a test per conversion.
2. **UTC with a zone in storage**; local time only at the edge (display, input), with the place's IANA zone (`Asia/Ho_Chi_Minh`), never a fixed offset.
3. **Idempotency keys** derived from the shipment on every carrier write call; retries never book twice.
4. **Explicit shipment state machine**; carrier events deduplicated by id and applied in event-time order.
5. **Rate cards are versioned data** with effective dates; every surcharge has a golden number from the carrier's card.
6. **Chargeable weight = max(actual, dimensional)** with the carrier's divisor and rounding rule.
7. **Addresses and phone numbers are personal data**: never in logs; driver locations kept only as long as needed.
8. **Each carrier in its own adapter**; a missing capability ⇒ named refusal.

## 4. Sample mutant suite

```toml
zone = "F"
cmd = "PYTHONPATH=src python -m pytest -q tests/rating tests/units"

[[mutant]]
id = "lb-kg-01"
file = "src/units/convert.py"
find = "KG_PER_LB = Decimal(\"0.45359237\")"
replace = "KG_PER_LB = Decimal(\"0.5\")"
why = "a rounded conversion constant ⇒ every rate in lb is off by 10%"

[[mutant]]
id = "dimweight-01"
file = "src/rating/chargeable.py"
find = "return max(actual_kg, dimensional_kg)"
replace = "return actual_kg"
why = "bulky light parcels are charged on actual weight ⇒ systematic under-billing"

[[mutant]]
id = "cutoff-01"
file = "src/sla/cutoff.py"
find = "now_utc = datetime.now(timezone.utc)"
replace = "now_utc = datetime.now()"
why = "cut-off compared in the server's local time ⇒ orders roll to the wrong day"
```
