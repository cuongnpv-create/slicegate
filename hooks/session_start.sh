#!/usr/bin/env bash
# SessionStart của plugin slicegate. Chỉ ĐỌC, luôn exit 0 (⛔ chặn mở phiên).
# Dự án chưa có slicegate.toml ⇒ im lặng. Hook riêng của dự án (.slicegate/hooks/session_start.sh) đã in báo cáo khi
# tìm được `slicegate` trên PATH ⇒ im lặng để khỏi in hai lần; không tìm được (chỉ cài plugin) ⇒ plugin in thay.
PROJECT="${CLAUDE_PROJECT_DIR:-$PWD}"
[ -f "$PROJECT/slicegate.toml" ] || [ -f "$PROJECT/gatekit.toml" ] || exit 0
if [ -f "$PROJECT/.claude/settings.json" ] && grep -qE "(slicegate|gatekit)/hooks/session_start.sh" "$PROJECT/.claude/settings.json" \
   && command -v slicegate >/dev/null 2>&1; then
  exit 0
fi
"${CLAUDE_PLUGIN_ROOT}/bin/slicegate" --root "$PROJECT" report --brief 2>/dev/null || true
exit 0
