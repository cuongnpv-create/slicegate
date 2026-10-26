"""Nhật ký guard: guard nào đã bắt được lỗi thật; lớp lỗi nào đã nổ mấy lần.

Luật đẻ guard mới: lớp lỗi phải nổ ≥ 3 lần THẬT (dòng `incident` cùng `subject`) và guard phải có selftest ca âm.
Guard 0 lần bắt sau thời gian dài = ứng viên gỡ (guard cũng tốn chi phí).
Sổ TSV: `date · kind{guard-catch|incident} · subject · source · description`.
"""
from __future__ import annotations

import datetime as dt
from collections import Counter

from gatekit.config import Config
from gatekit.messages import t

HEADER = "date\tkind\tsubject\tsource\tdescription\n"
KINDS = ("guard-catch", "incident")
THRESHOLD = 3


def rows(cfg: Config) -> list[dict]:
    p = cfg.root / cfg["guard_log"]
    if not p.exists():
        return []
    out = []
    for ln in p.read_text(encoding="utf-8").splitlines():
        if not ln.strip() or ln.startswith("#") or ln.startswith("date\t"):
            continue
        c = (ln.split("\t") + [""] * 5)[:5]
        out.append(dict(zip(("date", "kind", "subject", "source", "description"), c)))
    return out


def record(cfg: Config, kind: str, subject: str, source: str, description: str) -> None:
    if kind not in KINDS:
        raise ValueError(t("hygiene.bad_kind", kinds=KINDS))
    for v in (subject, source, description):
        if "\t" in v or "\n" in v:
            raise ValueError(t("hygiene.bad_field"))
    p = cfg.root / cfg["guard_log"]
    p.parent.mkdir(parents=True, exist_ok=True)
    if not p.exists():
        p.write_text(HEADER, encoding="utf-8")
    with p.open("a", encoding="utf-8") as f:
        f.write(f"{dt.date.today().isoformat()}\t{kind}\t{subject}\t{source}\t{description}\n")


def report(cfg: Config, guard_names: list[str]) -> str:
    rs = rows(cfg)
    catches = Counter(r["subject"] for r in rs if r["kind"] == "guard-catch")
    incidents = Counter(r["subject"] for r in rs if r["kind"] == "incident")
    lines = [t("hygiene.catches")]
    for g in sorted(set(guard_names) | set(catches)):
        lines.append(f"  {catches.get(g, 0):>3}  {g}")
    lines.append(t("hygiene.incidents", n=THRESHOLD))
    for subj, n in incidents.most_common():
        mark = t("hygiene.eligible") if n >= THRESHOLD else ""
        lines.append(f"  {n:>3}  {subj}{mark}")
    return "\n".join(lines)
