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
if command -v gatekit >/dev/null 2>&1; then GK=(gatekit); else GK=(python3 -m gatekit); fi
"${GK[@]}" report --brief 2>/dev/null || echo "(gatekit not installed — pip install gatekit)"
echo
echo "── 🌿 GIT ──"
echo "   branch: $(git branch --show-current 2>/dev/null) · HEAD $(git rev-parse --short HEAD 2>/dev/null)"
echo "   uncommitted files: $(git status --porcelain 2>/dev/null | wc -l)"
echo "   worktrees: $(git worktree list 2>/dev/null | wc -l)"
