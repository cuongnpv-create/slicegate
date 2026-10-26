---
name: check
description: Run every slicegate guard on the current repository and fix or explain each failure — guards, mutant anchors, duplicate ledger ids, debt, slice ratio. Use when the user asks to check, verify or "make slicegate green", or before committing/pushing a slice.
argument-hint: "[--fast]"
allowed-tools: Bash(slicegate:*) Bash(git:*) Read Grep Glob Edit
---

# Run the slicegate checks

The `slicegate` command is on your PATH. Talk to the user in the project's language (`slicegate.toml` → `project.language`).

1. Run `slicegate check --full` (or `slicegate check --fast` if `$ARGUMENTS` says so), then `slicegate report`.
2. For each RED item, find the cause in the code (file:line) and fix it **in the code** when the fix is clear:
   - `test_wiring` — declare the test in its lane manifest (`tests/manifest.tsv`: path, lane, tier 0–4).
   - `naming_scope` — rename the identifier to English. The baseline file is only for names that existed before slicegate.
   - `secret_leak` — stop the secret reaching print/log/raise/f-string; read secrets from files or env. Allowlist only
     with a written reason, and tell the user.
   - `locale_parity` — add the missing keys in every language with the same `{params}`.
   - `provider_name_scope` / `partition_key_scope` — move provider-specific code into its adapter; add the partition column.
   - `legacy_import_ban` — copy the legacy code with a source label instead of importing it.
   - `migration_scope` — never edit a pinned migration: revert it and write a new one; `slicegate migrations lock` for new files.
   - `mutant_anchors` — update the mutant's `find` to the current code (exactly one occurrence), keeping what it removes.
   - `ledger_ids` — two entries with the same id: renumber the newer one with `slicegate ledger alloc`.
3. Never weaken a guard, add a broad allowlist entry, or drop a test to get green. If a fix is not yours to make
   (design decision, owner's call), stop and say exactly what is red and why.
4. Re-run until GREEN and show the final output.
