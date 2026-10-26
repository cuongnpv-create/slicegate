"""Phần chung của máy gác.

Hợp đồng mỗi guard (module trong `gatekit/guards/`, tên không bắt đầu bằng `_`):
  NAME: str            tên guard
  PACK: str | None     None = lõi; khác = chỉ chạy khi gói ấy bật trong `project.packs`
  FAST: bool           True = đủ rẻ để chạy ở pre-commit
  DEFECT: str          khuyết tật MÃ nó chặn (luật "quản trị phải chặn được lỗi mã")
  check(cfg) -> list[Finding]
  selftest() -> list[str]   rỗng = XANH; mỗi phần tử = một ca âm/dương hỏng

Fail-closed: lỗi Python trong guard ⇒ tính ĐỎ (cli bắt ngoại lệ).
"""
from __future__ import annotations

import os
import subprocess
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

from gatekit.config import Config, from_dict
from gatekit.messages import t


@dataclass(frozen=True)
class Finding:
    guard: str
    path: str
    line: int
    message: str

    def __str__(self) -> str:
        loc = f"{self.path}:{self.line}" if self.line else self.path
        return f"[{self.guard}] {loc} — {self.message}"


def is_git(root: Path) -> bool:
    return (root / ".git").exists()


def git(root: Path, *args: str, check: bool = True) -> str:
    r = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True)
    if check and r.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)}: {r.stderr.strip()}")
    return r.stdout


def iter_files(cfg: Config, *, exts: tuple[str, ...] | None = None) -> Iterator[str]:
    """Tệp tương đối (dấu `/`) thuộc cây làm việc: git ls-files -co --exclude-standard; ngoài git ⇒ os.walk."""
    root = cfg.root
    if is_git(root):
        rels = git(root, "ls-files", "-co", "--exclude-standard").splitlines()
    else:
        rels = []
        for d, dirs, files in os.walk(root):
            dirs[:] = [x for x in dirs if x != ".git"]
            for f in files:
                rels.append(os.path.relpath(os.path.join(d, f), root).replace(os.sep, "/"))
    for rel in sorted(set(rels)):
        if cfg.excluded(rel):
            continue
        if exts and not rel.endswith(exts):
            continue
        if (root / rel).is_file():
            yield rel


def read(cfg: Config, rel: str) -> str:
    return (cfg.root / rel).read_text(encoding="utf-8", errors="replace")


@contextmanager
def fixture(files: dict[str, str], over: dict | None = None, *, git_init: bool = False) -> Iterator[Config]:
    """Thư mục tạm có sẵn tệp — dùng cho --selftest và pytest."""
    with tempfile.TemporaryDirectory(prefix="gatekit-fx-") as d:
        root = Path(d)
        for rel, body in files.items():
            p = root / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(body, encoding="utf-8")
        if git_init:
            subprocess.run(["git", "-C", d, "init", "-q", "-b", "main"], check=True)
        yield from_dict(root, over or {})


def expect(errors: list[str], label: str, findings: list[Finding], *, red: bool) -> None:
    """Ghi lỗi selftest nếu kết quả ngược kỳ vọng."""
    if red and not findings:
        errors.append(t("selftest.want_red", label=label))
    if not red and findings:
        errors.append(t("selftest.want_green", label=label, first=findings[0]))
