# slicegate

**English** · [Tiếng Việt](https://github.com/cuongnpv-create/slicegate/blob/main/README.vi.md)

*Every slice of AI-written code passes a gate.*

A gated development process for teams of AI coding agents (Claude Code): small slices, independent gates, an
append-only verdict ledger, guards that run in git hooks, and **mutation testing by risk zone** to prove the tests
actually guard the rules.

It was extracted from a real project — a multi-exchange trading platform built by several agents working in parallel —
by separating the **mechanism** (reusable) from the project-specific **content**. Every project parameter lives in one
file: `slicegate.toml`.

> Status: `0.3.0` (formerly **gatekit**) — core + 10 industry packs. Document templates, CLI and guard messages in
> **English and Vietnamese**; identifiers in code are English.

## Why

AI agents write code fast, but they fail in four recurring ways. slicegate blocks each one with something **measurable**:

| Failure | What slicegate does |
|---|---|
| "Done" claimed without evidence | G-IN / G-OUT packets require the measuring command + file coordinates; gates review the diff, never a conclusion |
| Hollow tests (code tested against itself) | mutants run on a copy, chosen by risk zone T/K/F; `test_wiring` catches tests nothing runs |
| Parallel sessions stepping on each other | one coordinator session is the only ledger writer; id ranges reserved up front; one worktree per slice; commits queue |
| Process growing bigger than the code | "conditions with teeth" (every condition must name the code defect it blocks) · `quota` on governance-vs-code slices · ledger rolling |

## What it looks like

An agent writes a pallet quote with a bare `weight` and a cut-off built from `datetime.utcnow()`:

```python
def quote(weight, distance_km):
    cutoff = datetime.utcnow().replace(hour=10, minute=0)
    total_weight = weight * 1.1
    return cutoff, total_weight * distance_km
```

The pre-commit hook (logistics pack) blocks the commit:

```
$ git commit -m "feat(rating): pallet pricing [S-14]"
🔴 naive_time — 1 violation(s) (blocks: timestamps without a time zone ⇒ cut-offs, SLAs and ETAs shift by the server's time zone)
   [naive_time] src/shipping/pallet.py:5 — `datetime.utcnow()` creates a timestamp without a time zone — pass `timezone.utc` / `tzinfo=`
🔴 unit_suffix — 2 violation(s) (blocks: quantities without units ⇒ kg/lb, km/mi, °C/°F get mixed: wrong rates, overloaded vehicles, spoiled cold chain)
   [unit_suffix] src/shipping/pallet.py:4 — quantity `weight` carries no unit in its name (e.g. `_kg`, `_km`, `_cbm`, `_c`) ∨ `units: ignore <reason>`
   [unit_suffix] src/shipping/pallet.py:6 — quantity `total_weight` carries no unit in its name (e.g. `_kg`, `_km`, `_cbm`, `_c`) ∨ `units: ignore <reason>`
pre-commit: 🔴 slicegate check --fast RED
```

Every guard states the **code defect** it blocks, and every guard ships with negative-case self-tests.

## Install

### Option 1 — Claude Code plugin (recommended)

```
/plugin marketplace add cuongnpv-create/slicegate
/plugin install slicegate@slicegate
```
Outside a session: `claude plugin marketplace add cuongnpv-create/slicegate && claude plugin install slicegate@slicegate`.

The plugin brings:

| Component | Use |
|---|---|
| `/slicegate:init` | asks for level, packs, languages, lanes ⇒ runs `slicegate init` ⇒ fills `CLAUDE.md`, `[zones]` and the test manifest from your real code ⇒ `check --full` GREEN |
| `/slicegate:check` | runs every guard and fixes each RED in the code (never by loosening the guard) |
| `/slicegate:gate G-IN\|G-OUT\|G-DECIDE <slice>` | measure · allocate an id · pick the gate · send the packet · record the verdict |
| `/slicegate:coordinator` | opens a coordinator session per `SESSION_PROTOCOL` |
| `slicegate` command | on Bash's PATH inside Claude Code — no pip needed (Python ≥ 3.11 only) |
| `SessionStart` hook | prints a status summary when a session opens in a project that uses slicegate |

`slicegate hooks install` run from the plugin writes the command's path into the git hooks, so `pre-commit` /
`pre-push` also work for commits made outside Claude Code. After a plugin update (the path changes), run
`slicegate hooks install` again. Note: claude.ai and Cowork do not install plugins with a `bin/` directory — this plugin
is for Claude Code.

### Option 2 — pip

```bash
pip install slicegate                                               # or: pipx install slicegate · uvx slicegate
cd your-project && git init                                         # if it is not a repo yet
slicegate init --name "MyApp" --language en --level standard --pack i18n --pack postgres
slicegate hooks install
slicegate check --full
```

Agents talking in another language but documents in English: `--language ja --docs-language en`.

After `init`: fill in `CLAUDE.md §1/§2/§7`, declare `[zones]` in `slicegate.toml` from your real code, then open a
coordinator session with `docs/governance/COORDINATOR_PROMPT.md`.

## Levels

| Level | Agents | Verdict ledger | Fits |
|---|---|---|---|
| `lite` | chief-architect · qa-lead | — (STATUS + CHANGELOG only) | small app, one person |
| `standard` | + security-lead · ux-gate · product-director · design-director | per lane | teams, several agents in parallel |
| `regulated` | + compliance-officer | per lane | finance, health, sensitive data |

## Industry packs

| Pack | Adds |
|---|---|
| `i18n` | guard `locale_parity` (complete catalogs, matching keys and parameters) · article "localized from day one" |
| `multi_provider` | guards `provider_name_scope`, `partition_key_scope` · articles "the provider is explicit", "intent → route → translate", "unknown is not no" |
| `legacy_upgrade` | guard `legacy_import_ban` · `LEGACY_UPGRADE_GUIDE.md` (COPY / UPGRADE / REPLACE / NEW labels, source labels, behaviour-capture tests) |
| `postgres` | guard `migration_scope` (pinned sha, contiguous numbering) · `slicegate migrations lock` |
| `fintech` | agents `execution-lead` (zone T), `quant-lead` (zone F), `domain-auditor` |
| `data_pipeline` | agent `data-integrity` |
| `ecommerce` | guards `money_float` (no floating-point money — Python, SQL, `parseFloat`), `pci_scope` (never store card numbers / CVV) · agents `checkout-lead` (zone T: orders, payments, webhooks, refunds, stock), `pricing-lead` (zone F: prices, promotions, tax, rounding) · `ECOMMERCE_GUIDE.md` · Article 12 "Money is exact" |
| `saas_multitenant` | guards `tenant_scope` (tenant tables carry the tenant column; every SQL statement in code that touches one filters by tenant — Python, JS/TS, Go, Java…, `.sql` files), `tenant_rls` (with `require_rls`: tenant tables enable Row Level Security and have a policy) · agents `tenancy-lead` (zone K), `billing-lead` (zone T/F) · `SAAS_GUIDE.md` · Article 13 "The tenant is explicit" |
| `healthcare` | guards `phi_log` (no health data in print / log / raise / analytics / error trackers — Python, JS/TS), `phi_tag` (SQL health-data columns carry a `-- phi` tag ⇒ a data map) · agents `privacy-lead` (zone K), `clinical-safety-lead` (zone F) · `HEALTHCARE_GUIDE.md` · Article 14 "Health data is minimal and traceable" |
| `logistics` | guards `unit_suffix` (quantity names carry their unit: `weight_kg`, `distanceKm`, `temp_c` — Python, JS/TS, SQL), `naive_time` (no naive timestamps: `datetime.utcnow()`, `now()` without tz, SQL `timestamp`, JS `new Date("… hh:mm")`) · agents `fulfillment-lead` (zone T), `routing-lead` (zone F) · `LOGISTICS_GUIDE.md` · Article 15 "Quantities and times are unambiguous" |

## Commands

```
slicegate init        set the process up in a repo (never overwrites existing files without --force)
slicegate check       enabled guards · --fast (pre-commit) · --full (+ mutant anchors + duplicate ledger ids)
slicegate selftest    negative / positive cases of every guard (--all: packs not enabled too)
slicegate zone        risk zone of a diff + the testing it requires; T/K files without a standing mutant suite ⇒ RED
slicegate mutants     anchors · plan · run [--changed BASE]   (MUT_ONLY=id,… to pick)
slicegate ledger      alloc (reserve an id range) · check (duplicates) · open (OPEN conditions) · roll
slicegate debt        debt entries missing columns / overdue
slicegate quota       ratio of governance slices to code slices
slicegate hygiene     report · record — what each guard caught, which defect class has fired 3 times (enough for a new guard)
slicegate report      summary (the SessionStart hook uses --brief)
slicegate migrate     move a project set up under the old name gatekit (see below)
```

## Languages

| Setting | Meaning |
|---|---|
| `project.language` | the language agents talk in (any, e.g. `en`, `vi`, `ja`) |
| `project.docs_language` | language of the document templates: `en` · `vi`; empty = follow `language` when a template set exists, else `en` |

CLI, guard and tool messages use the same language (`src/slicegate/messages.py`); override one run with
`SLICEGATE_LANG=en|vi`. Tests `test_template_parity` and `test_messages` keep both languages in lockstep: same files and
keys, same placeholders and parameters, no Vietnamese left in the `en` set.

## Migrating from gatekit

Before `0.3.0` this tool was called **gatekit**. Projects set up under that name keep working: `gatekit.toml` and the
`.gatekit/` directory are still read (with a reminder), the `gatekit` command still exists when installed with pip (with a
reminder), and `GATEKIT_LANG` is still honoured. To move for good:

```bash
slicegate migrate     # git mv gatekit.toml → slicegate.toml, .gatekit/ → .slicegate/, rewrite hooks, reinstall git hooks
git commit -m "chore: migrate gatekit → slicegate"
```

The `gatekit` command and reading the old names will be removed in a later release.

## slicegate guards itself

This repo runs slicegate on itself (`slicegate.toml` at level lite, `tests/manifest.tsv`, `mutants/`):
`slicegate check --full` GREEN · 271 pytest tests · **25/25 mutants killed** on the guards and the decision rules
(risk zones, slice quota, ledger id allocation, ledger rolling, the mutant runner).

When this mutant suite was first built, the first run reported 11/11 "survived": the test command in the copy imported
the `pip -e` package, which pointed back at the original checkout, so the mutants had no effect. `slicegate mutants run`
now warns when every mutant survives.

## Case study

[`docs/case-studies/itsdangerous.md`](https://github.com/cuongnpv-create/slicegate/blob/main/docs/case-studies/itsdangerous.md) (in Vietnamese) — slicegate set up on
`pallets/itsdangerous`: 6 zone-K mutants exposed a real test gap in key rotation (all 297 tests stayed green with half of
the key-trial loop removed); 3 slicegate rough edges found and fixed on the spot (first `check` went from 12 false REDs to 0).

## Layout

```
.claude-plugin/        plugin.json · marketplace.json · icon.png (the repo is both the plugin and its marketplace)
bin/slicegate          the plugin's command (runs src/ directly)
skills/                /slicegate:init · check · gate · coordinator
hooks/                 the plugin's SessionStart hook
src/slicegate/
  config.py            slicegate.toml → defaults + validation
  messages.py          message catalog en · vi, one t() function
  guards/              guards (core + packs); each has check() · selftest() · DEFECT
  tools/               ledger · debt · slice_quota · risk_zone · guard_hygiene
  qa/mutants.py        mutants on a copy, selected by diff, anchor checks
  scaffold.py          slicegate init / migrate (templates with {{KEY}}, {{#level …}}, {{#pack …}})
  templates/<vi|en>/   CLAUDE.md · governance/ · per-lane ledgers · core agents · hooks
  packs/<pack>/<vi|en>/ agents + documents of each industry pack
tests/                 pytest
mutants/               slicegate's own mutant suites
```

## Roadmap

- More packs: `mobile`.
- A dashboard over verdict ledgers, OPEN conditions and the guard catch log.

## License

[MIT](https://github.com/cuongnpv-create/slicegate/blob/main/LICENSE).
