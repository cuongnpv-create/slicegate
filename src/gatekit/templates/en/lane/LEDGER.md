# LEDGER — lane `{{LANE_NAME}}` (prefix `{{LANE_PREFIX}}`) · {{PROJECT}}

Gate verdicts, append-only. The ONLY writer: the lane's coordinator session. Numbers come from `gatekit ledger alloc`.
CLOSED entries older than `ledger.roll_keep_days` are moved to `archive/` by `gatekit ledger roll` — the live ledger only holds open work.

Entry template:

```
## {{LANE_PREFIX}}-L<n> — <G-IN|G-OUT|G-DECIDE> <slice id> · <YYYY-MM-DD>
Status: OPEN | CLOSED
Role: <gate> · measured rev: <sha> · recorded by: coordinator
VERDICT: APPROVE | APPROVE-WITH-CONDITIONS | REJECT | NEEDS-INFO
Assessment: …
Conditions:
- **{{LANE_PREFIX}}-C<n>** [OPEN] <CODE defect it blocks> · measure: <command/test> · zone: <T|K|F|other>
Remarks (not conditions): …
NEXT / ASSIGNMENT: ① … ② …
```

---
