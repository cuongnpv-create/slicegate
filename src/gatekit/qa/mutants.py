"""Đột biến trên BẢN SAO — chứng minh test thật sự canh luật, không phải test rỗng.

Bộ đột biến = một tệp TOML trong `mutants.dir`:

    zone = "K"                                  # vùng của bộ (T/K/F/khác)
    cmd = "python -m pytest -q tests/test_auth.py"   # lệnh mặc định cho mọi đột biến của bộ

    [[mutant]]
    id = "auth-01"
    file = "src/auth/login.py"
    find = "if not verify(password, user.hash):"     # NEO: phải xuất hiện ĐÚNG 1 lần trong tệp
    replace = "if False:"
    why = "gỡ cổng kiểm mật khẩu ⇒ ai cũng đăng nhập được"   # khuyết tật mà đột biến mô phỏng
    # cmd = "…"            (tuỳ chọn, ghi đè lệnh của bộ)
    # targets = ["…"]      (tuỳ chọn, tệp mà đột biến canh — mặc định [file]; dùng để chọn theo diff)

Mỗi đột biến: chép cây làm việc ra thư mục tạm (⛔ đụng checkout thật) → sửa đúng 1 đoạn → chạy lệnh → PHẢI ĐỎ
(rc ≠ 0) = BỊ GIẾT. rc = 0 ⇒ SỐNG ⇒ test không canh luật ấy. Trước bộ: chạy lệnh trên bản sao CHƯA đột biến — phải
XANH và đo thời gian (ngân sách `tests.budget.mutant_seconds`).
"""
from __future__ import annotations

import fnmatch
import shutil
import subprocess
import tempfile
import time
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from gatekit.config import Config
from gatekit.messages import t

ZONE_ALIASES = {"khác": "other"}   # bộ đột biến viết bằng nhãn tiếng Việt vẫn đọc được
_IGNORE = shutil.ignore_patterns(".git", "node_modules", ".venv", "__pycache__", ".pytest_cache", ".claude")


@dataclass
class Mutant:
    suite: str
    id: str
    file: str
    find: str
    replace: str
    cmd: str
    why: str = ""
    targets: list[str] = field(default_factory=list)


@dataclass
class Suite:
    path: str
    zone: str
    mutants: list[Mutant]


def load_suites(cfg: Config) -> list[Suite]:
    d = cfg.root / cfg["mutants"]["dir"]
    out: list[Suite] = []
    if not d.is_dir():
        return out
    for f in sorted(d.glob("*.toml")):
        rel = f.relative_to(cfg.root).as_posix()
        with f.open("rb") as fh:
            data = tomllib.load(fh)
        default_cmd = data.get("cmd", "")
        ms = []
        for m in data.get("mutant", []):
            cmd = m.get("cmd", default_cmd)
            if not cmd:
                raise ValueError(t("mutants.no_cmd", suite=rel, id=m.get("id")))
            ms.append(Mutant(rel, m["id"], m["file"], m["find"], m["replace"], cmd, m.get("why", ""),
                             list(m.get("targets", [m["file"]]))))
        out.append(Suite(rel, ZONE_ALIASES.get(data.get("zone", "other"), data.get("zone", "other")), ms))
    return out


def anchor_problems(cfg: Config, suites: list[Suite] | None = None) -> list[str]:
    """Neo lệch (đoạn `find` không còn đúng 1 lần) ⇒ đột biến chết im lặng. Rẻ — chạy ở pre-push."""
    out = []
    ids: dict[str, str] = {}
    for s in suites if suites is not None else load_suites(cfg):
        for m in s.mutants:
            if m.id in ids:
                out.append(t("mutants.dup_id", suite=s.path, id=m.id, other=ids[m.id]))
            ids[m.id] = s.path
            p = cfg.root / m.file
            if not p.exists():
                out.append(t("mutants.no_file", suite=s.path, id=m.id, file=m.file))
                continue
            n = p.read_text(encoding="utf-8").count(m.find)
            if n != 1:
                out.append(t("mutants.anchor_count", suite=s.path, id=m.id, n=n, file=m.file))
            if not m.why:
                out.append(t("mutants.no_why", suite=s.path, id=m.id))
    return out


def select(suites: list[Suite], changed_files: list[str] | None, only: list[str] | None = None) -> list[Mutant]:
    """Chọn đột biến bị ảnh hưởng: tệp đích ∩ diff, hoặc tệp bộ đột biến đổi. `changed_files=None` ⇒ ĐỦ."""
    picked: list[Mutant] = []
    for s in suites:
        for m in s.mutants:
            if only is not None:
                if m.id in only:
                    picked.append(m)
                continue
            if changed_files is None or s.path in changed_files or any(
                    fnmatch.fnmatchcase(c, tgt) or c == tgt for c in changed_files for tgt in m.targets):
                picked.append(m)
    if only is not None:
        unknown = set(only) - {m.id for m in picked}
        if unknown:
            raise ValueError(t("mutants.unknown_only", ids=sorted(unknown)))
    return picked


@dataclass
class Result:
    mutant: Mutant
    status: str      # KILLED · SURVIVED · TIMEOUT · ANCHOR
    seconds: float


def _run(cmd: str, cwd: Path, timeout: float) -> tuple[int | None, float]:
    t0 = time.monotonic()
    try:
        r = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, timeout=timeout)
        return r.returncode, time.monotonic() - t0
    except subprocess.TimeoutExpired:
        return None, time.monotonic() - t0


def run(cfg: Config, mutants: list[Mutant], *, timeout: float | None = None, log=print) -> list[Result]:
    budget = cfg["tests"]["budget"]
    per = float(budget["mutant_seconds"])
    timeout = timeout or max(per * 10, 30.0)
    results: list[Result] = []
    with tempfile.TemporaryDirectory(prefix="gatekit-mut-") as d:
        copy = Path(d) / "tree"
        shutil.copytree(cfg.root, copy, ignore=_IGNORE, symlinks=True)
        baseline_done: set[str] = set()
        for m in mutants:
            if m.cmd not in baseline_done:
                rc, secs = _run(m.cmd, copy, timeout)
                if rc != 0:
                    raise RuntimeError(t("mutants.baseline_red", cmd=m.cmd, rc=rc))
                if secs > per:
                    log(t("mutants.slow", cmd=m.cmd, secs=secs, per=per))
                baseline_done.add(m.cmd)
            target = copy / m.file
            orig = target.read_text(encoding="utf-8")
            if orig.count(m.find) != 1:
                results.append(Result(m, "ANCHOR", 0.0))
                log(t("mutants.anchor_drift", id=m.id, file=m.file))
                continue
            target.write_text(orig.replace(m.find, m.replace, 1), encoding="utf-8")
            try:
                rc, secs = _run(m.cmd, copy, timeout)
            finally:
                target.write_text(orig, encoding="utf-8")
            status = "TIMEOUT" if rc is None else ("KILLED" if rc != 0 else "SURVIVED")
            results.append(Result(m, status, secs))
            log(f"  {status:<9} {m.id}  ({secs:.1f}s)  {m.why}")
    return results
