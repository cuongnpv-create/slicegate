# GATE PROTOCOL — {{PROJECT}}

> Current law, written clean. The history of rule changes lives in `docs/CHANGELOG.md`, not here.
> Parameters (risk zones, test budgets, parallelism, ledger lanes) live in `gatekit.toml` — the single source.

## §1 — When a gate is required

**The default is to DO.** Routine work within an opened scope (bug fixes, more tests, local cleanup) ⇒ do → measure →
one line in STATUS. Gates are only for **consequential** work:

| Work | Primary gate | Co-gate |
|---|---|---|
| Open a phase / first slice of a phase · architecture change · new service or new running revision | `chief-architect` | domain gate |
| Slice touching zone **T** (irreversible actions: money, orders, deleting user data) | the zone's domain gate (industry pack) ∨ `chief-architect` | `chief-architect` |
| Slice touching zone **K** (secrets · keys · authentication · permissions) | `security-lead` | `chief-architect` when architecture is touched |
| Slice touching zone **F** (formulas · decision rules) | the formula domain gate (industry pack) ∨ `qa-lead` | — |
| DDL / DCL / manual DML on a database holding data | `chief-architect` | domain gate of the table |
| UI touching money / risk / deletion | `ux-gate` | the matching domain gate |
| Legal conditions, consent, ToS, library licences | `compliance-officer` (regulated level) | — |
| Changing the process itself (`CLAUDE.md`, this file, agents, hooks, guards) | `chief-architect` | — |
| Closing a session | `chief-architect` | — |

**Primary gate by slice type** — a slice touching several types takes the gate of the HEAVIEST type as primary, the rest
become co-gates: `service/DDL/zone T` > `main gate/CI/hooks` > `QA tools/guards` > `pure domain (formulas, UI)`.

**Widening SCOPE does not widen AUTHORITY:** the owner saying "just do it" does not remove the gate on consequential work.

## §2 — Report package (slice author → gate)

```
PACKAGE <G-IN | G-OUT | G-DECIDE | G-OUT SESSION-CLOSE> — <slice id>
Numbers: <P>-L<n> · <P>-C<a>…<b> [· <P>-D<n>]     ← the coordinator allocates a range FIRST (gatekit ledger alloc); the gate never picks numbers
Rev: <git rev-parse --short HEAD> · branch <name>
1. Work / scope — files · functions · tables · services, coordinates from `grep -n` (never eyeballed)
2. What the user can do now that they could not before
3. Evidence: every number = measuring command + UTC timestamp + scope scanned
4. Risk zone: output of `gatekit zone --base <base>` + the form of testing delivered per §4
5. DoD + negative cases (expectations from a source OUTSIDE the code: spec, contract, book, legacy system with line refs) — run on a COPY
6. Risks · external API call limits (if any) · rollback path
7. Open conditions from earlier gates that touch this slice
8. Clock: RED n/2 · YELLOW m/6
```

The gate receives **files, diff, coordinates, measuring commands** — never the author's conclusions. The gate opens the
files itself and re-measures when cheap.

## §3 — Verdicts

`APPROVE` · `APPROVE-WITH-CONDITIONS` · `REJECT` · `NEEDS-INFO`. A REJECT must carry all 7 lines:
`SCOPE · BLOCKING-INVARIANT · EVIDENCE (file:line / number) · REMEDIATION-REQUIRED · RETEST · UNBLOCK-AUTHORITY · DECISION-NEXT`.

- **Rule in ONE pass**, with an executable path forward. A hard part ⇒ answer with HOW, not with why it cannot be done.
- **Missing parameter / source** ⇒ the gate PROPOSES one with its rationale; the owner approves in one line. Never park a slice to ask.
- **DoD must be measured against an INDEPENDENT source.** Reject a DoD that agrees with itself (tests comparing code to itself — circular).
- At every G-OUT, `chief-architect` adds an **ASSIGNMENT** block: ≥ 2 next slices by priority, ≥ 1 of them runnable while
  other tracks are blocked (waiting for data, waiting for people). Never "waiting for the owner to pick the next slice".

### §3.1 — Gate conditions must have TEETH

Every condition `<P>-C<n>` states all 3 parts:

1. **The CODE defect it blocks** — the concrete wrong behaviour a user / money / data would suffer;
2. **The measurement** — the command or test proving it is closed;
3. **The risk zone** — T / K / F / other.

Rules that come with it:
- Missing part 1 ⇒ the condition is invalid: the author asks to drop it at G-OUT with a one-line reason. In zones T/K the
  gate MUST answer in writing (add the part ∨ drop with reason); no answer ⇒ the condition STAYS (fail-closed).
- Two conditions blocking the SAME defect ⇒ merge them. No ceiling, no floor on the number of conditions. A number range
  is a reservation, not a quota.
- A worry that cannot be tied to a concrete defect ("just in case", "to be safe") ⇒ write it as a REMARK in the verdict, never as a condition.
- **Conditions are CLOSED inside the slice.** No `post-merge`, no "next slice" for things that can be fixed now. A gate
  that sets a condition expects it closed before the slice closes — or it does not set it.
- Recorded in the LEDGER as: `- **<P>-C<n>** [OPEN|CLOSED] <defect> · measure: <command> · zone: <T/K/F/other>`.

### §3.2 — Debt

Never open debt for something solvable inside the slice. Open debt ONLY when it is **unsolvable inside the slice** (it
must wait for another code slice); the debt states the defect left open · a measurable close condition · the slice that
will close it · a due date — and is **closed as soon as the condition holds**. `gatekit debt` measures it.

## §4 — Risk zones T · K · F (form of testing)

A slice belongs to a zone when a file in its diff matches `zones.<Z>.paths` ∨ an added line matches `zones.<Z>.grep`
(`gatekit zone --base <base>`). The heaviest zone decides. A new file carrying money / keys / formulas outside the regex ⇒
the domain gate assigns the zone AT G-IN and the slice updates `gatekit.toml` in the SAME commit. Co-gates may only ADD
to a zone; removing = `chief-architect` G-DECIDE.

| Zone | Required at G-OUT |
|---|---|
| **T** | a PERMANENT mutant suite (in the manifest); a mutant removing each gate **at each call site** ⇒ RED; negative cases for every refusal path |
| **K** | a PERMANENT mutant suite; missing permission ⇒ named refusal; secrets never in logs (`secret_leak` GREEN) |
| **F** | INDEPENDENT golden numbers (book, published table, analytic answer) as a permanent test + ≥ 1 mutant hitting the formula core; editing a golden test ⇒ re-run that column/rule's mutants |
| **other** | behaviour tests + ≥ 1 negative case with an expectation from OUTSIDE the code. Mutants not required; the gate MAY demand them when it suspects an empty test — naming the TEST and the reason, ≤ {{MAX_ONE_OFF}} mutants, run ONCE |

- T/K suites may not be removed from the manifest nor added to a "known anchor drift" list — drift ⇒ fix it in the slice.
- **Only the owner may relax:** per-call-site mutants in zone T · permanent T/K suites · independent golden numbers · negative cases in every slice.
- Removing an old suite outside T/K: run it ONCE at `<base>`; any SURVIVING mutant ⇒ do not remove; add a test that kills it first.

## §5 — Hot-path performance

Hot paths = `hotpath.paths`. A slice touching a hot path that HAS a bench: run the bench at `<base>` then `<rev>`, same
machine, `{{HOT_RUNS}}` runs each, record p50/p99. RED when ⒜ an absolute budget is exceeded ∨ ⒝ p50`<rev>` ≥
`{{HOT_RATIO}}×` p50`<base>` and the two ranges do not overlap. No stored baseline files (machines drift). Total
measuring time ≤ `{{HOT_MAX}}` seconds per slice. No bench yet ⇒ not RED; the domain gate decides which slice builds the
first one. Correct first, fast second — performance never replaces correctness tests.

## §6 — Test budget per slice

Tier 1 (pure) ≤ `{{T1}}` s · one mutant ≤ `{{MUT1}}` s (time the command BEFORE running the suite) · all mutants ≤ `{{MUTALL}}` s.
Over budget ⇒ stop and fix the CAUSE by cutting cost only (narrow the command, cheap test-double plus a test pinning the real
thing, split expensive cases); never drop tests, never lower production thresholds. The author runs the FULL suite ONCE on
the candidate sha and submits the log; the gate runs `--check` + reads the log + ≤ 3 mutants of its choice (`MUT_ONLY=<id,…>`).
Re-run in FULL only when the log is missing / the sha differs / something SURVIVED.

## §7 — Numbering

| Id | Meaning | Defined at |
|---|---|---|
| `<P>-L<n>` | verdict entry | `## <P>-L<n> — <title> · <YYYY-MM-DD>` in the lane's `LEDGER.md` |
| `<P>-D<n>` | durable ruling | `## <P>-D<n> — …` in `DECISIONS.md` |
| `<P>-C<n>` | gate condition | `- **<P>-C<n>** [OPEN\|CLOSED] …` inside an entry |
| `<P>-N<n>` | debt | a table row in `DEBT.md` |

Lanes and prefixes: {{LANES_INLINE}}. Numbers are allocated by the **coordinator** with `gatekit ledger alloc` — primary
gate ≥ `{{RANGE_PRIMARY}}` C ids, co-gate `{{RANGE_CO}}`. Unused numbers in a range are normal. `gatekit ledger check` catches duplicates.

## §8 — Session clock

Declare `RED n/2 · YELLOW m/6` every turn (RED = serious mistake: false claim, bypassing a gate; YELLOW = minor slip). At the
limit ⇒ **open NO new slice · accept NO new work; the slice IN PROGRESS must be COMPLETED** (fix gate conditions → G-OUT →
into main) → FINALLY the session G-OUT → full STATUS handoff (slices done, SHAs, open conditions) → commit → push. Never stop mid-slice.

## §9 — Where bytes live

- Code enters `main` only after G-OUT. `main` = approved bytes.
- RUNNING bytes = SIGNED bytes: deploy from a rev in `main`, never from a working tree; code that has not passed G-OUT is never present where production runs.
- Mutants / breakage experiments run on a COPY (`gatekit mutants run` copies for you), never on the working checkout.
