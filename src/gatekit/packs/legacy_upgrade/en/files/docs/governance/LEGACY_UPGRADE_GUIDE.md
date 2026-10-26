# LEGACY_UPGRADE_GUIDE — upgrading from a legacy system ({{PROJECT}})

Acceptance principle: **whatever the legacy system could do, the new system can do; whatever it could not, the new system can.**
The default is **KEEP + UPGRADE** legacy code (copy with a source label, then modify). Rewrite only with evidence from the closed list in §2.

## 1. Five principles (priority order when they conflict)
1. No legacy business rule / edge case is lost in the move — every feature gets a named decision.
2. Never import legacy code (`legacy_import_ban`); bringing it over = COPY with a source label + tests in the new system.
3. Legacy behaviour is captured by tests (characterization) BEFORE changing it.
4. Upgrades are NAMED ITEMS (e.g. "U-03 add the tenant dimension to keys"), never "rewrite it nicer".
5. Progress is measured in numbers: files with source labels / total files; features with a decision / total features.

## 2. A verdict label for every file in the new system
| Label | Meaning | Evidence at G-OUT |
|---|---|---|
| `COPY` | carried as-is | source line right above the copied block |
| `UPGRADE` | carried + modified | source line + upgrade item id |
| `REPLACE` | rewritten | evidence from the closed list below + ruling id |
| `NEW` | the legacy system did not have it | a `grep` over the legacy system proving it |

**CLOSED list for REPLACE:** ⒜ legacy code violates a hard constraint of the new system, with evidence (e.g. the UI calls
external services directly, business logic in the client, fake data) · ⒝ the legacy formula is wrong per the book (audit
with numbers) · ⒞ a dead dependency / unpatchable security issue · ⒟ the owner ruled that part be rewritten.

**Feature decisions:** CARRY · CARRY-MODIFIED · MERGE · DEFER (condition) · DROP (reason).

## 3. Source label
```
# {{LEGACY_LABEL}}<rev or nogit-md5:<8 chars>>:<file>:<first-line>-<last-line>
# upgrade: U-<n> <description of the upgrade item>
```
(TS/JS use `//`). Placed RIGHT above the copied block. G-OUT measures: a `COPY`/`UPGRADE` file where
`grep -c "{{LEGACY_LABEL}}"` = 0 ⇒ RED.

## 4. "Carried from legacy" table in G-IN
| New-system file | Label | Legacy source (file:line) | Upgrade item | Characterization test |
|---|---|---|---|---|

## 5. One upgrade slice
1. Inventory the legacy subsystem's features (file:line) → a named decision for each feature.
2. Write tests capturing the legacy behaviour (input → the legacy system's real output) — expectations from OUTSIDE the new code.
3. Copy with labels → run the characterization tests (GREEN) → apply each upgrade item → tests for each item.
4. G-OUT: the "carried from legacy" table + label measurement + features not carried have a DROP/DEFER decision.
