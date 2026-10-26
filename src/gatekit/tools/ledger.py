"""Sổ phán theo làn: cấp DẢI số, kiểm số trùng, cuộn sổ.

Mã số (mỗi làn một tiền tố, `ledger.lanes`):
  <P>-L<n>  entry phán (tiêu đề `## <P>-L<n> — <tiêu đề> · <YYYY-MM-DD>` trong LEDGER.md)
  <P>-D<n>  ruling bền (tiêu đề `## <P>-D<n> — …` trong DECISIONS.md)
  <P>-C<n>  điều kiện gate (định nghĩa ở đầu gạch đầu dòng: `- **<P>-C<n>** …`)
  <P>-N<n>  nợ (dòng bảng `| <P>-N<n> | …` trong DEBT.md)

Luật cấp số: người ĐIỀU PHỐI cấp dải TRƯỚC khi gọi gate; gate ⛔ tự chọn số (va số khi hai phiên song song cùng
đọc đuôi sổ). Dải ghi vào `.gatekit/reservations.tsv`; số dư của dải là bình thường, ⛔ phải lấp.
"""
from __future__ import annotations

import datetime as dt
import re
from collections import defaultdict
from pathlib import Path

from gatekit.config import Config

KINDS = {"L": "LEDGER.md", "D": "DECISIONS.md", "C": "LEDGER.md", "N": "DEBT.md"}
RES_FILE = ".gatekit/reservations.tsv"
RES_HEADER = "date\tlane\tkind\tstart\tend\towner\tnote\n"


def _lane(cfg: Config, name: str) -> dict:
    for ln in cfg.lanes():
        if ln["name"] == name:
            return ln
    raise KeyError(f"làn lạ `{name}` — có: {[x['name'] for x in cfg.lanes()]}")


def _def_patterns(prefix: str) -> dict[str, re.Pattern]:
    p = re.escape(prefix)
    return {
        "L": re.compile(rf"^##\s+{p}-L(\d+)\b", re.M),
        "D": re.compile(rf"^##\s+{p}-D(\d+)\b", re.M),
        "C": re.compile(rf"^\s*[-*]\s+\*\*{p}-C(\d+)\*\*", re.M),
        "N": re.compile(rf"^\|\s*{p}-N(\d+)\s*\|", re.M),
    }


def _text(cfg: Config, lane: dict, kind: str) -> str:
    texts = []
    base = cfg.root / lane["dir"]
    for f in [base / KINDS[kind], *sorted((base / "archive").glob(KINDS[kind].replace(".md", "-*.md")))]:
        if f.exists():
            texts.append(f.read_text(encoding="utf-8"))
    return "\n".join(texts)


def used(cfg: Config, lane_name: str, kind: str) -> list[int]:
    lane = _lane(cfg, lane_name)
    return [int(x) for x in _def_patterns(lane["prefix"])[kind].findall(_text(cfg, lane, kind))]


def reservations(cfg: Config) -> list[dict]:
    p = cfg.root / RES_FILE
    if not p.exists():
        return []
    rows = []
    for ln in p.read_text(encoding="utf-8").splitlines()[1:]:
        if not ln.strip():
            continue
        c = ln.split("\t")
        rows.append({"date": c[0], "lane": c[1], "kind": c[2], "start": int(c[3]), "end": int(c[4]),
                     "owner": c[5] if len(c) > 5 else "", "note": c[6] if len(c) > 6 else ""})
    return rows


def alloc(cfg: Config, lane_name: str, kind: str, count: int, owner: str, note: str = "") -> tuple[int, int]:
    if kind not in KINDS:
        raise ValueError(f"loại lạ `{kind}` — có {sorted(KINDS)}")
    if count < 1:
        raise ValueError("count ≥ 1")
    _lane(cfg, lane_name)  # làn lạ ⇒ KeyError
    top = max([0, *used(cfg, lane_name, kind),
               *[r["end"] for r in reservations(cfg) if r["lane"] == lane_name and r["kind"] == kind]])
    start, end = top + 1, top + count
    p = cfg.root / RES_FILE
    p.parent.mkdir(parents=True, exist_ok=True)
    if not p.exists():
        p.write_text(RES_HEADER, encoding="utf-8")
    with p.open("a", encoding="utf-8") as f:
        f.write(f"{dt.date.today().isoformat()}\t{lane_name}\t{kind}\t{start}\t{end}\t{owner}\t{note}\n")
    return start, end


def duplicates(cfg: Config) -> list[str]:
    """Số được ĐỊNH NGHĨA > 1 lần trong cùng làn/loại (kể cả phần đã cuộn vào archive)."""
    out = []
    for lane in cfg.lanes():
        for kind in KINDS:
            counts: dict[int, int] = defaultdict(int)
            for n in used(cfg, lane["name"], kind):
                counts[n] += 1
            for n, c in sorted(counts.items()):
                if c > 1:
                    out.append(f"{lane['prefix']}-{kind}{n} định nghĩa {c} lần (làn {lane['name']})")
    return out


_ENTRY = re.compile(r"^## (?P<id>\S+-L\d+)\b.*?·\s*(?P<date>\d{4}-\d{2}-\d{2})\s*$", re.M)


def roll(cfg: Config, lane_name: str, *, today: dt.date | None = None, dry_run: bool = False) -> list[str]:
    """Chuyển entry ĐÃ ĐÓNG (`Trạng thái: CLOSED` ∨ `Status: CLOSED`) cũ hơn `roll_keep_days` sang `archive/LEDGER-<YYYY>Q<q>.md`.

    Entry còn điều kiện mở (`Trạng thái: OPEN`) ở lại sổ sống — gate chỉ phải đọc sổ sống + DECISIONS.
    """
    lane = _lane(cfg, lane_name)
    path = cfg.root / lane["dir"] / "LEDGER.md"
    if not path.exists():
        return []
    today = today or dt.date.today()
    keep = dt.timedelta(days=int(cfg["ledger"]["roll_keep_days"]))
    text = path.read_text(encoding="utf-8")
    heads = list(_ENTRY.finditer(text))
    if not heads:
        return []
    head_text = text[:heads[0].start()]
    keep_parts, moved = [head_text], defaultdict(list)
    for i, m in enumerate(heads):
        body = text[m.start(): heads[i + 1].start() if i + 1 < len(heads) else len(text)]
        d = dt.date.fromisoformat(m.group("date"))
        closed = re.search(r"^(Trạng thái|Status):\s*CLOSED\b", body, re.M) is not None
        if closed and today - d > keep:
            moved[f"{d.year}Q{(d.month - 1) // 3 + 1}"].append((m.group("id"), body))
        else:
            keep_parts.append(body)
    ids = [i for parts in moved.values() for i, _ in parts]
    if dry_run or not ids:
        return ids
    arch = cfg.root / lane["dir"] / "archive"
    arch.mkdir(parents=True, exist_ok=True)
    for q, parts in moved.items():
        f = arch / f"LEDGER-{q}.md"
        prev = f.read_text(encoding="utf-8") if f.exists() else f"# LEDGER lưu trữ {q} — làn {lane_name}\n\n"
        f.write_text(prev + "".join(b if b.endswith("\n") else b + "\n" for _, b in parts), encoding="utf-8")
    path.write_text("".join(keep_parts), encoding="utf-8")
    return ids


def open_conditions(cfg: Config, lane_name: str) -> list[str]:
    """Điều kiện chưa đóng: gạch `- **<P>-C<n>** … [OPEN]`."""
    lane = _lane(cfg, lane_name)
    p = re.escape(lane["prefix"])
    rx = re.compile(rf"^\s*[-*]\s+\*\*({p}-C\d+)\*\*(.*\[OPEN\].*)$", re.M)
    return [f"{m.group(1)}{m.group(2)}" for m in rx.finditer(_text(cfg, lane, "C"))]


def lane_dir(cfg: Config, lane_name: str) -> Path:
    return cfg.root / _lane(cfg, lane_name)["dir"]
