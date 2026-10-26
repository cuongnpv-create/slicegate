"""Vùng rủi ro của một lát: T · K · F · khác — quyết HÌNH THỨC kiểm mà lát phải nộp ở G-OUT.

  T  thao tác không đảo ngược (gửi lệnh, ghi tiền, xoá dữ liệu): bộ đột biến THƯỜNG TRỰC, gỡ từng cổng TẠI TỪNG chỗ gọi.
  K  bí mật · khoá · xác thực · quyền xem: bộ đột biến THƯỜNG TRỰC.
  F  công thức · quy tắc quyết định: số vàng nguồn ĐỘC LẬP (test thường trực) + ≥ 1 đột biến.
  khác: test hành vi + ≥ 1 ca âm có kỳ vọng từ nguồn NGOÀI mã; đột biến chỉ khi gate nghi test rỗng (≤ 3, chạy một lần).
Vùng nặng nhất quyết. Nguồn DUY NHẤT của regex: `[zones]` trong gatekit.toml.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from gatekit.config import Config
from gatekit.guards._common import git

ORDER = ("T", "K", "F")
REQUIREMENTS = {
    "T": "bộ đột biến THƯỜNG TRỰC trong manifest; đột biến gỡ từng cổng tại TỪNG chỗ gọi ⇒ ĐỎ; ca âm cho mọi đường từ chối",
    "K": "bộ đột biến THƯỜNG TRỰC trong manifest; ca âm: thiếu quyền ⇒ từ chối có tên; bí mật ⛔ ra log",
    "F": "số vàng nguồn ĐỘC LẬP (sách/bảng công bố/đáp án giải tích) là test thường trực + ≥ 1 đột biến đánh lõi công thức",
    "khác": "test hành vi + ≥ 1 ca âm có kỳ vọng từ nguồn NGOÀI mã; đột biến chỉ khi gate nêu TÊN test nghi rỗng (≤ 3, một lần)",
}


@dataclass
class ZoneReport:
    files: dict[str, list[str]] = field(default_factory=dict)   # vùng -> tệp
    grep_hits: dict[str, list[str]] = field(default_factory=dict)

    @property
    def heaviest(self) -> str:
        for z in ORDER:
            if self.files.get(z) or self.grep_hits.get(z):
                return z
        return "khác"

    def zones(self) -> list[str]:
        zs = [z for z in ORDER if self.files.get(z) or self.grep_hits.get(z)]
        return zs or ["khác"]


def classify_files(cfg: Config, files: list[str], added_lines: dict[str, list[str]] | None = None) -> ZoneReport:
    rep = ZoneReport()
    added_lines = added_lines or {}
    for z in ORDER:
        spec = cfg["zones"].get(z, {})
        prx = [re.compile(p) for p in spec.get("paths", [])]
        grx = [re.compile(g) for g in spec.get("grep", [])]
        rep.files[z] = [f for f in files if any(p.search(f) for p in prx)]
        hits = []
        for f, lines in added_lines.items():
            for ln in lines:
                if any(g.search(ln) for g in grx):
                    hits.append(f"{f}: {ln.strip()[:120]}")
                    break
        rep.grep_hits[z] = hits
    return rep


def changed(cfg: Config, base: str, rev: str = "HEAD") -> tuple[list[str], dict[str, list[str]]]:
    files = git(cfg.root, "diff", "--name-only", f"{base}..{rev}").splitlines()
    added: dict[str, list[str]] = {}
    cur = None
    for ln in git(cfg.root, "diff", "-U0", f"{base}..{rev}").splitlines():
        if ln.startswith("+++ b/"):
            cur = ln[6:]
            added.setdefault(cur, [])
        elif ln.startswith("+") and not ln.startswith("+++") and cur:
            added[cur].append(ln[1:])
    return [f for f in files if not cfg.excluded(f)], added


def classify(cfg: Config, base: str, rev: str = "HEAD") -> ZoneReport:
    files, added = changed(cfg, base, rev)
    return classify_files(cfg, files, added)
