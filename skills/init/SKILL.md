---
name: init
description: Set up the gatekit gated development process in the current repository — interview the owner (level, packs, languages, ledger lanes), run `gatekit init`, then fill in the project-specific parts (CLAUDE.md §1/§2/§7, risk zones) from the real code. Use when the user asks to install, adopt or set up gatekit in a project.
argument-hint: "[project name]"
allowed-tools: Bash(gatekit:*) Bash(git:*) Read Grep Glob Edit Write AskUserQuestion
---

# Set up gatekit in this repository

The `gatekit` command is on your PATH (it comes with this plugin). Talk to the user in their language.

## 1. Check the ground
- `git rev-parse --show-toplevel` — must be a git repository; if not, ask before running `git init`.
- If `gatekit.toml` already exists, gatekit is installed: stop and offer `/gatekit:check` instead. `gatekit init` never
  overwrites files, but do not run it twice by accident.
- Survey the repo briefly (top-level dirs, languages, test runner, DB migrations, i18n catalogs, payment/auth code).

## 2. Ask the owner (one AskUserQuestion call, propose a recommended option for each)
- **Level** — `lite` (1 person, small app: architect + QA gates only) · `standard` (team / parallel agents, ledgers per
  lane) · `regulated` (money, health, sensitive data: adds compliance).
- **Packs** (multi-select, recommend from what you saw): `i18n` · `multi_provider` · `legacy_upgrade` · `postgres` ·
  `fintech` · `data_pipeline` · `ecommerce` (shops: payments, orders, refunds, pricing) · `saas_multitenant` (tenant isolation, plans & billing) · `healthcare` (patient data privacy, clinical safety — pair it with level `regulated`) · `logistics` (shipping, warehouses, fleets: units, time zones, carrier integrations).
- **Languages** — the language agents talk in (`--language`) and the document templates (`--docs-language vi|en`).
- **Lanes** (standard/regulated only) — e.g. one lane `core:P`, or `core:P be:PB fe:PF` when BE and FE run in parallel.

Project name: `$ARGUMENTS` if given, else the repository directory name.

## 3. Install
```bash
gatekit init --name "<name>" --level <level> [--pack <p> ...] --language <lang> [--docs-language <vi|en>] [--lane name:PREFIX ...]
gatekit hooks install
```

## 4. Make it the project's own (do this yourself, from the real code — do not leave placeholders)
- `gatekit.toml`
  - `[paths] prod` — regexes for production code dirs.
  - `[zones.T]` — irreversible actions (payments, orders, deletes); `[zones.K]` — auth, secrets, permissions;
    `[zones.F]` — formulas / decision rules. Use real paths you found; show the user the list.
  - pack sections (`[packs.i18n]`, `[packs.postgres]`, …) — point them at the real directories.
- `CLAUDE.md §1` (what the project is), `§2` (hard constraints — only machine-checkable ones), `§7` (protected zones).
- `tests/manifest.tsv` — one line per existing test file or glob, with lane and tier.

## 5. Prove it
- `gatekit check --full` must be GREEN. Typical first-run reds and the right fix:
  - `test_wiring` — add the tests to `tests/manifest.tsv`;
  - `naming_scope` on legacy code — list existing names in `.gatekit/naming_baseline.txt` (it can only shrink);
  - `migration_scope` — `gatekit migrations lock` after reviewing the migrations;
  - `secret_leak` — fix the leak; allowlist (`.gatekit/secret_allowlist.txt`) only with a reason.
- Commit everything as one governance slice, e.g. `chore: install gatekit [G-1]`.
- Tell the user: what was installed, what you filled in, and that `/gatekit:coordinator` starts a coordinator session.
