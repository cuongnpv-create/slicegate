# HEALTHCARE_GUIDE — healthcare industry rules ({{PROJECT}})

Supplements `GATE_PROTOCOL`. Primary gates: `privacy-lead` (health data, zone K), `clinical-safety-lead` (clinical
numbers, zone F). Use the `regulated` level to get `compliance-officer`. This document is engineering law, not legal advice.

## 1. Suggested risk zones (declare them in `gatekit.toml`)

| Zone | Typical code | Example regex |
|---|---|---|
| K | patient records, access control, access logs, sharing, data export | `'^src/(patients?|records?|access|audit|sharing|exports?)/'` |
| F | dosing, unit conversion, reference ranges, risk scores, alerts | `'^src/(dosing|units|labs?|risk|alerts?)/'` |
| T | outgoing prescriptions, booking / cancelling appointments, insurance claims | `'^src/(prescriptions?|scheduling|claims?)/'` |

## 2. The pack's guards

| Guard | Blocks |
|---|---|
| `phi_log` | health data in print / log / raise / analytics / error trackers (Python, JS/TS) |
| `phi_tag` | SQL health-data columns without a `-- phi` tag (data map: `grep -rn -- "-- phi" db/`) |

## 3. Hard rules

1. **Minimum necessary:** access by role + care relationship; APIs return only the fields needed.
2. **Log every read** of a record (who · when · patient · fields · reason), append-only.
3. **Break-glass access** with a mandatory reason, an alert, a later review.
4. **PHI never leaves the protected zone:** logs, analytics, error trackers, push notifications, emails carry internal ids only.
5. **PHI columns are tagged and encrypted** per policy; encryption keys are kept apart from the database.
6. **No real data in dev/test**; use synthetic or de-identified data.
7. **Explicit units** for every clinical quantity; conversions through one module.
8. **Clinical formulas cite a source + golden numbers from that source**; out-of-range values ⇒ named refusal.

## 4. Sample mutant suite

```toml
zone = "K"
cmd = "PYTHONPATH=src python -m pytest -q tests/access tests/clinical"

[[mutant]]
id = "care-rel-01"
file = "src/access/policy.py"
find = "if not has_care_relationship(user, patient):"
replace = "if False:"
why = "drops the care-relationship check ⇒ every clinician can read every record"

[[mutant]]
id = "read-audit-01"
file = "src/records/service.py"
find = "audit.record_read(user, patient, fields, reason)"
replace = "pass"
why = "reading a record leaves no trace"

[[mutant]]
id = "units-01"
file = "src/units/convert.py"
find = "MCG_PER_MG = 1000"
replace = "MCG_PER_MG = 1"
why = "mg ↔ mcg mix-up ⇒ a 1000× dosing error"
```
