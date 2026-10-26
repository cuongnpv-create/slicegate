#!/usr/bin/env bash
# SessionStart — gatekit. Chỉ ĐỌC. In: khối đầu STATUS · điều kiện OPEN · trạng thái git.
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$ROOT" || exit 0
echo "🎯 {{PROJECT}} — đọc: CLAUDE.md → docs/STATUS.md → docs/governance/GATE_PROTOCOL.md"
echo
if [ -f docs/STATUS.md ]; then
  echo "── ▶️ STATUS (khối mới nhất) ──"
  awk '/^## S[0-9]+ /{n++} n==1{print} n>1{exit}' docs/STATUS.md | head -20
  echo
fi
# Không có gatekit trên PATH (vd chỉ cài plugin Claude Code) ⇒ bỏ qua; hook SessionStart của plugin in thay.
if command -v gatekit >/dev/null 2>&1; then gatekit report --brief 2>/dev/null; fi
echo
echo "── 🌿 GIT ──"
echo "   nhánh: $(git branch --show-current 2>/dev/null) · HEAD $(git rev-parse --short HEAD 2>/dev/null)"
echo "   tệp chưa commit: $(git status --porcelain 2>/dev/null | wc -l)"
echo "   worktree: $(git worktree list 2>/dev/null | wc -l)"
