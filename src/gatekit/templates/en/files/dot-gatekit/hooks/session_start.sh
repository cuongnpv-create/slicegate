#!/usr/bin/env bash
# SessionStart — gatekit. READ-ONLY. Prints: latest STATUS block · OPEN conditions · git state.
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$ROOT" || exit 0
echo "🎯 {{PROJECT}} — read: CLAUDE.md → docs/STATUS.md → docs/governance/GATE_PROTOCOL.md"
echo
if [ -f docs/STATUS.md ]; then
  echo "── ▶️ STATUS (latest block) ──"
  awk '/^## S[0-9]+ /{n++} n==1{print} n>1{exit}' docs/STATUS.md | head -20
  echo
fi
# No gatekit on PATH (e.g. only the Claude Code plugin is installed) ⇒ skip; the plugin's SessionStart hook prints it.
if command -v gatekit >/dev/null 2>&1; then gatekit report --brief 2>/dev/null; fi
echo
echo "── 🌿 GIT ──"
echo "   branch: $(git branch --show-current 2>/dev/null) · HEAD $(git rev-parse --short HEAD 2>/dev/null)"
echo "   uncommitted files: $(git status --porcelain 2>/dev/null | wc -l)"
echo "   worktrees: $(git worktree list 2>/dev/null | wc -l)"
