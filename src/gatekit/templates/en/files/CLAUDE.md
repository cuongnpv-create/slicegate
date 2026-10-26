# CLAUDE.md — {{PROJECT}}

Instructions for agents working in this repository. **Communicate in: {{LANGUAGE}}.**
Process: gatekit (level `{{LEVEL}}`{{PACKS_SUFFIX}}). Parameters live in `gatekit.toml` — the single source.

---

## §0 — At the start of every session, read in order

1. `CLAUDE.md` (this file) — rules, process, document map.
2. `docs/STATUS.md` — the ONLY live status + handoff to the next session.
3. `docs/governance/GATE_PROTOCOL.md` — when requesting / receiving a gate verdict.
{{#level standard regulated}}4. `docs/governance/SESSION_PROTOCOL.md` — when coordinating several agents.
{{/level}}

The `SessionStart` hook prints: the latest STATUS block, open conditions, git state.

---

## §1 — What this project is

<!-- Fill in: product, users, scope, legacy system (if any), where it runs. One paragraph. -->

---

## §2 — Hard architectural constraints

<!-- Fill in the project's MACHINE-CHECKABLE rules; each rule names the guard that enforces it. Enabled by packs: -->
- **Naming:** identifiers in code (files, functions, classes, variables) are English/ASCII; the authors' language belongs in comments, docs and user-facing strings. Enforced by: `naming_scope`.
- **Secrets:** no secret literals in the repo; secrets never reach logs / stdout / error messages. Enforced by: `secret_leak`.
- **Missing capability ⇒ named refusal** (reason code) — never `return None`, never pretend it worked.
{{#pack i18n}}- **Localized from day one:** every user-facing string goes through the `{{I18N_DIR}}/` catalog in {{I18N_LANGS}} in the SAME slice. The server returns `{code, message_key, params}`, never sentences. Enforced by: `locale_parity`.
{{/pack}}{{#pack multi_provider}}- **Multi-provider:** a provider's name lives only in its adapter; every table carries the partition column. Enforced by: `provider_name_scope`, `partition_key_scope`.
{{/pack}}{{#pack legacy_upgrade}}- **Legacy upgrade:** never import legacy code; bringing it over = copy with a source label `{{LEGACY_LABEL}}<rev>:<file>:<line>` right above the copied block + tests in the new system. Enforced by: `legacy_import_ban`. Guide: `docs/governance/LEGACY_UPGRADE_GUIDE.md`.
{{/pack}}{{#pack postgres}}- **Migrations:** a pinned migration is never edited — write a new one; numbering is contiguous. Enforced by: `migration_scope`.
{{/pack}}

---

## §3 — Process for every slice (MANDATORY)

```
survey (grep -n, real coordinates) ─► G-IN primary gate ─► code + tests + negative cases + mutants by RISK ZONE on a COPY
   ─► gatekit check ─► G-OUT primary gate (+ co-gates) ─► into main ─► ledger + STATUS in the SAME commit ─► report to owner ─► next slice ASSIGNED BY THE ARCHITECT
```

- **Default is to do.** Gates are only for consequential work (`GATE_PROTOCOL §1`).
- **Every slice states:** *what can the user do now that they could not do before*.
- **The risk zone decides the form of testing** (`gatekit zone --base main`, `GATE_PROTOCOL §4`).
- **Problems found on the way are fixed INSIDE the slice.** Debt only when it cannot be solved in the slice (`GATE_PROTOCOL §3.2`).
- **Governance exists to make code run correctly, not to make governance look good:** any new procedure / ledger / guard must name the CODE defect it blocks.
- Governance slices (0 production-code files) ≤ `{{GOV_MAX}}` in a row, then ≥ `{{CODE_AFTER_GOV}}` CODE slices (`gatekit quota`).
- **The chief architect assigns work PROACTIVELY** after every G-OUT — never ask the owner "what next".
- **Every number comes with the command that measured it + UTC timestamp + scope scanned.**
- **Session clock:** declare `RED n/2 · YELLOW m/6` every turn; at the limit ⇒ finish the slice in progress, open no new slice (`GATE_PROTOCOL §8`).
- Commits: the subject carries the slice id in square brackets, e.g. `feat(auth): two-step login [S-12]`.

---

## §4 — Owner rules (current)

Source: `docs/governance/OWNER_WORDS.md` (verbatim, append-only). The table below is the CURRENT law, written clean —
when a new order replaces an old one, edit the row; history lives in `OWNER_WORDS.md`.

| Id | Rule | Since |
|---|---|---|
| — | <!-- add a row when the owner gives an order --> | — |

---

## §5 — Gates and roles

| Role | Agent | Guards / owns |
|---|---|---|
{{AGENTS_TABLE}}

Agents live in `.claude/agents/`. The CREATOR (director) is never the GATE.

---

## §6 — Document map (every fact has exactly one owner)

| File | Owns | Updated |
|---|---|---|
| `CLAUDE.md` | rules, process, map | rarely |
| `gatekit.toml` | all process parameters (risk zones, budgets, lanes, packs) | when a parameter changes — through a gate |
| `docs/governance/CONSTITUTION.md` | supreme articles + where the machine enforces them | rarely |
| `docs/governance/GATE_PROTOCOL.md` | gate procedure | when the procedure changes |
{{#level standard regulated}}| `docs/governance/SESSION_PROTOCOL.md` | work session, coordinator session, per-lane tests | when the procedure changes |
| `docs/governance/OWNER_WORDS.md` | owner's words verbatim (append-only) | every owner order |
{{/level}}| `docs/governance/GUARD_CATCH_LOG.tsv` | real guard catches · incidents per defect class | `gatekit hygiene record` |
| `docs/STATUS.md` | live status + handoff | every slice |
| `docs/CHANGELOG.md` | milestones + rule changes | every milestone |
{{LEDGER_ROWS}}| `tests/manifest.tsv` | which test runs in which lane / tier | every new test |
| `mutants/*.toml` | mutant suites | T/K/F zone slices |

**Closing a session — update exactly:** `docs/STATUS.md` · `docs/CHANGELOG.md`{{#level standard regulated}} · the lane's `DEBT.md`{{/level}}; request the session G-OUT from `chief-architect`; commit; push.

---

## §7 — Protected zones

<!-- Fill in: read-only directories / services / databases; the legacy system; live environments. -->
- Code that has not passed G-OUT never runs where production runs; deploy only from a rev that is in `main`.
