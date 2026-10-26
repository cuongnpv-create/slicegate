"""Nợ: mỗi nợ MỞ phải có khuyết tật nó còn để ngỏ, điều kiện đóng đo được, lát sẽ đóng, hạn chưa qua.

Luật gốc: ⛔ mở nợ khi vấn đề giải được ngay trong lát; chỉ mở khi BẤT KHẢ GIẢI (phải chờ lát mã khác), và đóng
ngay khi thoả điều kiện — ⛔ để nợ trôi.

Bảng trong `<làn>/DEBT.md`:
| Mã | Nợ | Khuyết tật còn ngỏ | Điều kiện đóng | Lát đóng | Hạn | TT |
TT ∈ OPEN · CLOSED.
"""
from __future__ import annotations

import datetime as dt
import re

from gatekit.config import Config
from gatekit.tools.ledger import lane_dir
from gatekit.messages import t

_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def problems(cfg: Config, *, today: dt.date | None = None) -> list[str]:
    today = today or dt.date.today()
    out: list[str] = []
    for lane in cfg.lanes():
        p = lane_dir(cfg, lane["name"]) / "DEBT.md"
        if not p.exists():
            continue
        rx = re.compile(rf"^\|\s*({re.escape(lane['prefix'])}-N\d+)\s*\|(.*)\|\s*$")
        for ln in p.read_text(encoding="utf-8").splitlines():
            m = rx.match(ln)
            if not m:
                continue
            cols = [c.strip() for c in m.group(2).split("|")]
            if len(cols) < 6:
                out.append(t("debt.columns", id=m.group(1)))
                continue
            _, defect, close_cond, slice_id, due, status = cols[:6]
            if status.upper() != "OPEN":
                continue
            for label, v in (("debt.what_defect", defect), ("debt.what_condition", close_cond), ("debt.what_slice", slice_id)):
                if not v or v in {"-", "—", "?"}:
                    out.append(t("debt.missing", id=m.group(1), what=t(label)))
            if not _DATE.match(due):
                out.append(t("debt.bad_date", id=m.group(1), due=due))
            elif dt.date.fromisoformat(due) < today:
                out.append(t("debt.overdue", id=m.group(1), due=due))
    return out
