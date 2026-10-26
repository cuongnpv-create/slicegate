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
                out.append(f"{m.group(1)}: dòng thiếu cột (cần Nợ · Khuyết tật · Điều kiện đóng · Lát đóng · Hạn · TT)")
                continue
            _, defect, close_cond, slice_id, due, status = cols[:6]
            if status.upper() != "OPEN":
                continue
            for label, v in (("khuyết tật còn ngỏ", defect), ("điều kiện đóng", close_cond), ("lát đóng", slice_id)):
                if not v or v in {"-", "—", "?"}:
                    out.append(f"{m.group(1)}: nợ MỞ thiếu {label}")
            if not _DATE.match(due):
                out.append(f"{m.group(1)}: hạn `{due}` không phải YYYY-MM-DD")
            elif dt.date.fromisoformat(due) < today:
                out.append(f"{m.group(1)}: QUÁ HẠN {due}")
    return out
