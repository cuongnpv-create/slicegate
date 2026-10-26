"""Tỷ lệ lát QUẢN TRỊ : lát MÃ — "quản trị để mã chạy đúng, ⛔ để hệ quản trị đẹp".

Lát = các commit first-parent LIỀN NHAU mang cùng mã lát (`slices.id_regex` trong tiêu đề). Lát quản trị = chạm 0 tệp
mã sản xuất (`paths.prod`). Luật (tham số `session.*`):
  · chuỗi lát quản trị liền nhau ≤ `governance_slice_max`;
  · sau một chuỗi lát quản trị, cần ≥ `code_slices_after_governance` lát MÃ trước lát quản trị kế.
Miễn: tiêu đề mang `[QUOTA-EXEMPT: <lý do>]` (lý do bắt buộc, phải có lời owner/gate dẫn chứng).
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from gatekit.config import Config
from gatekit.guards._common import git

_EXEMPT = re.compile(r"\[QUOTA-EXEMPT:\s*\S[^\]]*\]")


@dataclass
class Slice:
    id: str
    commits: list[str]
    subjects: list[str]
    prod: bool
    exempt: bool

    @property
    def kind(self) -> str:
        return "MÃ" if self.prod else "QUẢN TRỊ"


def slices(cfg: Config, since: str | None = None, ref: str = "HEAD") -> list[Slice]:
    if not git(cfg.root, "rev-parse", "--verify", "-q", ref, check=False).strip():
        return []  # repo chưa có commit
    rng = f"{since}..{ref}" if since else ref
    log = git(cfg.root, "log", "--first-parent", "--reverse", "--format=%H%x09%s", rng).splitlines()
    rx = re.compile(cfg["slices"]["id_regex"])
    out: list[Slice] = []
    for line in log:
        sha, _, subj = line.partition("\t")
        m = rx.search(subj)
        sid = m.group("id") if m else f"(không mã) {sha[:8]}"
        files = git(cfg.root, "diff-tree", "--no-commit-id", "--name-only", "-r", "--root", sha).splitlines()
        prod = any(cfg.is_prod(f) for f in files)
        if out and out[-1].id == sid and m:
            s = out[-1]
            s.commits.append(sha)
            s.subjects.append(subj)
            s.prod = s.prod or prod
            s.exempt = s.exempt or bool(_EXEMPT.search(subj))
        else:
            out.append(Slice(sid, [sha], [subj], prod, bool(_EXEMPT.search(subj))))
    return out


def violations(cfg: Config, seq: list[Slice]) -> list[str]:
    gmax = int(cfg["session"]["governance_slice_max"])
    need = int(cfg["session"]["code_slices_after_governance"])
    out: list[str] = []
    run = 0            # số lát quản trị liền nhau hiện tại
    code_since = need  # số lát mã kể từ chuỗi quản trị gần nhất (khởi đầu coi như đủ)
    for s in seq:
        if s.prod:
            run = 0
            code_since += 1
            continue
        if s.exempt:
            continue
        if run == 0 and code_since < need:
            out.append(f"{s.id}: lát QUẢN TRỊ khi mới có {code_since}/{need} lát MÃ sau chuỗi quản trị trước")
        run += 1
        code_since = 0
        if run > gmax:
            out.append(f"{s.id}: {run} lát QUẢN TRỊ liền nhau (trần {gmax})")
    return out
