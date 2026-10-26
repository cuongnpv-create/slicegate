"""Guard `test_wiring` — mọi phép kiểm TỒN TẠI phải được khai ở manifest test (tức là có nơi THỰC SỰ chạy nó).

Lớp lỗi: "một test gác bất biến nhưng không ai chạy, và không ai biết" — test mới viết mà quên nối vào bộ chạy,
hoặc manifest còn trỏ tệp đã xoá (bộ chạy âm thầm bỏ qua).

Manifest (TSV, `tests.manifests` trong gatekit.toml): `đường dẫn|glob <TAB> làn <TAB> tầng <TAB> ghi chú`.
Tầng: 0 guard · 1 thuần · 2 DB/dịch vụ · 3 phát lại/E2E · 4 hợp đồng giữa làn.
"""
from __future__ import annotations

import fnmatch
import re

from gatekit.config import Config
from gatekit.guards._common import Finding, expect, fixture, iter_files, read
from gatekit.messages import t

NAME = "test_wiring"
PACK = None
FAST = True
DEFECT = {"vi": "test/bộ đột biến tồn tại nhưng không nằm trong manifest nào ⇒ không bao giờ chạy",
          "en": "a test/mutant suite exists but is in no manifest ⇒ it never runs"}

TIERS = {"0", "1", "2", "3", "4"}


def _entries(cfg: Config) -> tuple[list[tuple[str, str, int]], list[Finding]]:
    entries, found = [], []
    for man in cfg["tests"]["manifests"]:
        p = cfg.root / man
        if not p.exists():
            continue
        for i, raw in enumerate(read(cfg, man).splitlines(), 1):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            cols = raw.split("\t")
            if len(cols) < 3 or not cols[1].strip() or cols[2].strip() not in TIERS:
                found.append(Finding(NAME, man, i, t("test_wiring.bad_line")))
                continue
            entries.append((cols[0].strip(), man, i))
    return entries, found


def check(cfg: Config) -> list[Finding]:
    entries, found = _entries(cfg)
    files = list(iter_files(cfg))
    globs = [re.compile(g) for g in cfg["tests"]["test_globs"]]
    mut_dir = cfg["mutants"]["dir"].rstrip("/") + "/"
    targets = [f for f in files if any(g.search(f) for g in globs)
               or (f.startswith(mut_dir) and f.endswith(".toml"))]

    if targets and not any((cfg.root / m).exists() for m in cfg["tests"]["manifests"]):
        return [Finding(NAME, cfg["tests"]["manifests"][0], 0, t("test_wiring.no_manifest", n=len(targets)))]

    def matched(f: str) -> bool:
        return any(f == pat or fnmatch.fnmatchcase(f, pat) for pat, _, _ in entries)

    for f in targets:
        if not matched(f):
            found.append(Finding(NAME, f, 0, t("test_wiring.not_wired")))
    fileset = set(files)
    for pat, man, i in entries:
        if any(ch in pat for ch in "*?["):
            if not any(fnmatch.fnmatchcase(f, pat) for f in files):
                found.append(Finding(NAME, man, i, t("test_wiring.glob_empty", pat=pat)))
        elif pat not in fileset:
            found.append(Finding(NAME, man, i, t("test_wiring.stale", pat=pat)))
    return found


def selftest() -> list[str]:
    errs: list[str] = []
    ok = {"tests/test_a.py": "", "tests/manifest.tsv": "tests/test_a.py\tbe\t1\n"}
    with fixture(ok) as cfg:
        expect(errs, "đã khai", check(cfg), red=False)
    with fixture({"tests/test_a.py": "", "tests/test_b.py": "", "tests/manifest.tsv": "tests/test_a.py\tbe\t1\n"}) as cfg:
        expect(errs, "test_b chưa khai", check(cfg), red=True)
    with fixture({"tests/manifest.tsv": "tests/test_gone.py\tbe\t1\n"}) as cfg:
        expect(errs, "manifest trỏ tệp đã xoá", check(cfg), red=True)
    with fixture({"tests/test_a.py": "", "tests/manifest.tsv": "tests/*.py\tbe\t1\n"}) as cfg:
        expect(errs, "glob khớp", check(cfg), red=False)
    with fixture({"tests/test_a.py": "", "tests/manifest.tsv": "tests/test_a.py\tbe\n"}) as cfg:
        expect(errs, "thiếu cột tầng", check(cfg), red=True)
    with fixture({"mutants/auth.toml": "", "tests/manifest.tsv": ""}) as cfg:
        expect(errs, "bộ đột biến chưa khai", check(cfg), red=True)
    with fixture({"tests/test_a.py": ""}) as cfg:
        expect(errs, "không có manifest", check(cfg), red=True)
    return errs
