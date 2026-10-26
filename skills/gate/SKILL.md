---
name: gate
description: Prepare a gatekit gate package (G-IN before writing code, G-OUT before merging, or G-DECIDE for a question) for the current slice, send it to the right gate agent, and record the verdict in the lane ledger. Use when the user asks for a gate review, G-IN, G-OUT, or approval of a slice.
argument-hint: "<G-IN|G-OUT|G-DECIDE> <slice-id> [lane]"
allowed-tools: Bash(gatekit:*) Bash(git:*) Read Grep Glob Edit Write Agent
---

# Run a gate for a slice

Rules live in the project's `docs/governance/GATE_PROTOCOL.md` — read §1–§4 first. Arguments: `$ARGUMENTS`
(kind, slice id, optional lane; default lane = the first in `gatekit.toml`). Talk to the user in the project's language.

## 1. Measure (paste real output, never summaries)
- `git rev-parse --short HEAD`, current branch, `git diff --stat main...HEAD` (or the slice's base).
- `gatekit zone --base main` — heaviest zone and the form of testing it requires (T/K/F/other). T/K files without a
  permanent mutant suite are RED here: fix that before G-OUT.
- For G-OUT: test output of the lane's tiers, `gatekit check --full`, and `gatekit mutants run --changed main` log.
- `gatekit ledger open` — open conditions that touch this slice.

## 2. Allocate numbers (the gate never picks its own)
```bash
gatekit ledger alloc --lane <lane> --kind L --count 1 --owner coordinator --note "<slice-id> <kind>"
gatekit ledger alloc --lane <lane> --kind C --count 20 --owner coordinator --note "<slice-id> primary gate"
```

## 3. Choose the gate
Primary gate by the slice's heaviest type (`GATE_PROTOCOL §1`): service/DDL/zone T → `chief-architect` (or the
industry pack's money-path gate); zone K → `security-lead`; zone F → the formula gate or `qa-lead`; UI touching money
→ `ux-gate`. Use only agents that exist in `.claude/agents/`.

## 4. Send the package
Spawn the gate agent with a self-contained prompt following `GATE_PROTOCOL §2`: the numbers allocated, rev, scope with
`grep -n` coordinates, what the user can do now, evidence (command + UTC time + scope), zone output, DoD and negative
cases, risks, open conditions, clock. Give it **files, diff and commands — never your conclusions**. Tell it to answer
in the verdict format of its agent file and not to edit ledger files.

## 5. Record and act
- Append the verdict verbatim to `<lane dir>/LEDGER.md` as `## <P>-L<n> — <kind> <slice-id> · <YYYY-MM-DD>` with
  `Status: OPEN` while it has open conditions (`CLOSED` when none), `recorded by: coordinator`.
- Conditions must have teeth (defect · measurement · zone). Close every condition inside the slice before G-OUT.
- REJECT / NEEDS-INFO ⇒ fix and re-run this skill. APPROVE at G-OUT ⇒ merge, update `docs/STATUS.md` in the same
  commit, and run the next slice from the chief-architect's ASSIGNMENT.
