# SESSION_PROTOCOL — work session, roles, coordinator session ({{PROJECT}})

## 1. Roles

```
Owner — gives orders, decides what only the owner decides; owner's words recorded VERBATIM in docs/governance/OWNER_WORDS.md
  └─ COORDINATOR SESSION (one) — builds packages, allocates numbers, calls gates/agents, re-measures, writes ledgers, merges slices; never writes slice code
       ├─ CREATOR ROLES (never rule): product-director (BE: what, rules, API contracts) · design-director (FE: how it looks)
       ├─ SLICE AGENTS — one agent, one worktree per CODE slice
       └─ GATES (never write in their place): {{GATES_INLINE}}
```

- **CREATOR ≠ GATE.** Directors write specs and never rule; gates rule and never write in their place.
- **BE ↔ FE boundary:** BE writes features, rules, state machines, API contracts, named refusal codes; FE reads that
  contract to draw screens — a missing field ⇒ write a "request to BE", never invent an API.
- Slice agents never call directors; a missing spec ⇒ tell the coordinator ⇒ the coordinator calls (on the owner's word).

## 2. A work session

| # | Who | Work | Output |
|---|---|---|---|
| 1 | coordinator | read `CLAUDE.md §0` | **Morning brief**: what finished yesterday (SHAs), ≤ 3 questions only the owner can answer, plan |
| 2 | owner | answer / adjust the plan; silence ⇒ run the plan | owner's words into `OWNER_WORDS.md` |
| 3 | coordinator — **PLANNING MEETING, ONLY WHEN NEEDED** | new phase · roadmap change · < 2 slices of spec left · new product order from the owner. Order: product-director → chief-architect → design-director | specs + ASSIGNMENT |
| 4 | coordinator + agents + gates | slices per `CLAUDE.md §3`; after each G-OUT the chief-architect ASSIGNS work | ledgers + `STATUS` |
| 5 | coordinator | session G-OUT | **Evening brief**: slices done + SHAs, work in progress, questions for the owner |

## 3. The coordinator session

1. **One coordinator session** opened on `main`. It builds packages, allocates numbers, calls gates/agents, re-measures,
   writes ledgers, commits. It never writes slice code.
2. **The ONLY writer** of each ledger lane (`ledger.lanes`): gates and agents return verdicts/reports as text, the
   coordinator appends them verbatim (`recorded by: coordinator`). With several parallel sessions ⇒ split the lanes, each
   session writes only its own; shared files (`STATUS`, `OWNER_WORDS`, `CLAUDE.md`) — each side only appends its own block.
3. **Concurrency ceiling:** ≤ `{{MAX_CODE_SLICES}}` CODE slices being written · ≤ `{{MAX_AGENTS}}` agents in total (gates
   and surveys run within this). Cut off by API limits ⇒ lower the agent count, never stop mid-slice. Long jobs (24 h
   measurements, replays) run in the background and do not take an agent seat.
4. **One worktree per CODE slice** (`worktree_per_slice = {{WORKTREE}}`): `.claude/worktrees/<slice-id>`, branch
   `slice/<slice-id>`. Record the triple **slice id ↔ branch ↔ path** in `STATUS`. The agent edits only inside its worktree;
   never edits ledger files. Merging after G-OUT: rebase onto the latest `main` → `gatekit check` + the affected tests →
   `merge --ff-only` (no merge commits) → commit ledgers + STATUS with the SAME slice id → **remove** the worktree + branch at once.
5. **Commits queue:** one slice into `main` at a time, FIFO. Before its first byte, a slice declares the **shared files**
   it will touch (i18n catalog, reason codes, manifest, migration numbers) so two slices do not collide. Generated files
   are never conflict-resolved by hand — regenerate them.
6. **Independent gates:** a gate prompt hands over files, diff, coordinates, measuring commands — never the coordinator's
   conclusions. Full agent reports are written OUTSIDE the repo (e.g. `../meta/reports/<slice-id>/<role>-<n>.md`); the
   coordinator keeps the summary.
7. **Memory = `docs/STATUS.md`.** After each G-OUT write a new block: SHA, ledger ids used, work in progress, next
   ASSIGNMENT. Context nearly full ∨ clock limit reached ⇒ close the session + hand off, open no new slice.
8. **Measured entry:** `git status --porcelain` = 0 lines (another session's WIP ⇒ never clean it up, never stash; tell the
   owner) · `git worktree list` only shows worktrees whose owner is recorded in STATUS · latest STATUS block read.
9. Never `--no-verify`. A RED hook ⇒ fix it inside the slice's worktree.

## 4. Tests per lane — NEVER MERGED

| Tier | Content | Runs at |
|---|---|---|
| 0 | whole-tree guards (`gatekit check`) | `pre-commit` (fast) + `pre-push` (full + mutant anchors) |
| 1 | the lane's pure tests | every slice, within budget |
| 2 | the lane's DB / service tests (disposable containers, cleaned up including volumes) | slices touching the DB |
| 3 | replay / E2E (expensive) | only the owning lane |
| 4 | CONTRACT tests between lanes (BE↔FE, data↔BE) | in the tier-1 suite of BOTH lanes at the boundary |

One manifest per lane (`tests.manifests`), columns: `path · lane · tier · note`. `test_wiring` catches tests that exist
without a manifest entry. Budget: `GATE_PROTOCOL §6`.

## 5. Fixed limits

- Planning meetings **when needed**, never by default every morning.
- Governance slices (0 production-code files) ≤ `{{GOV_MAX}}` in a row; then ≥ `{{CODE_AFTER_GOV}}` CODE slices (`gatekit quota`).
- Every proposal for a new procedure / ledger / guard must name **the CODE defect it blocks**; if it cannot ⇒ do not do it.
