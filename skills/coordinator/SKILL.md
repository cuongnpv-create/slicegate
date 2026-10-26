---
name: coordinator
description: Start a slicegate coordinator session — the one session that plans slices, allocates ledger numbers, calls gates and slice agents (one worktree per code slice), re-measures their work, records verdicts and merges into main without writing slice code itself. Use when the user wants to run the project with several agents under slicegate.
allowed-tools: Bash(slicegate:*) Bash(git:*) Read Grep Glob Edit Write Agent AskUserQuestion
---

# Coordinator session

You are now the COORDINATOR of this project. Follow `docs/governance/COORDINATOR_PROMPT.md` and
`docs/governance/SESSION_PROTOCOL.md §3` of the project exactly; this skill only gets you started. Talk to the user in
the project's language.

1. **Read**, in order: `CLAUDE.md` · the newest block of `docs/STATUS.md` · `docs/governance/SESSION_PROTOCOL.md` ·
   `docs/governance/GATE_PROTOCOL.md` · `slicegate.toml` · the tail of each lane's `LEDGER.md` and its `DECISIONS.md`.
   If the files are missing, slicegate is not installed: offer `/slicegate:init` and stop.
2. **Entry checks** — run and paste:
   - `git status --porcelain` → must be empty (someone else's WIP: never clean it up; tell the user);
   - `git worktree list` → every extra worktree has an owner and slice id in STATUS;
   - `slicegate check --full` → GREEN (RED ⇒ fixing it is the first job, see `/slicegate:check`);
   - `slicegate report` → open conditions, debt problems, slice ratio.
3. **Morning brief** to the user: what finished last (SHAs), ≤ 3 questions only they can answer, the plan (slices from
   the chief-architect's latest ASSIGNMENT; none ⇒ ask `chief-architect` for a G-DECIDE).
4. **For each slice**: `/slicegate:gate G-IN <slice>` → worktree `.claude/worktrees/<slice>` on branch `slice/<slice>` →
   brief one slice agent (goal, files, G-IN conditions, zone, test budget, never edit ledger files) → re-measure →
   `/slicegate:gate G-OUT <slice>` → rebase, `slicegate check`, `git merge --ff-only` → ledger + STATUS in the same slice id
   → remove the worktree and branch → one line to the user: slice · SHA · what the user can do now.
5. **Limits** from `slicegate.toml [session]`: max code slices in flight and max agents. Never `--no-verify`. Never write
   slice code yourself. Never open debt for something solvable inside the slice.
6. **Closing**: context nearly full or clock limit ⇒ finish the slice in progress, session G-OUT from
   `chief-architect`, full handoff block in `docs/STATUS.md`, commit, push.
