"""Guard `naming_scope` — định danh trong mã (tên tệp, hàm, lớp, biến) phải ASCII/tiếng Anh; ngôn ngữ người viết
chỉ ở chú thích, tài liệu, chuỗi hiển thị.

Đường cơ sở (`naming.baseline`, mỗi dòng `tệp:tên`) MIỄN các tên đã có lúc lập guard trên mã cũ — và CHỈ CO LẠI:
mục không còn trong mã ⇒ ĐỎ cho tới khi xoá khỏi baseline (để baseline không thành chỗ giấu tên mới).
"""
from __future__ import annotations

import io
import re
import tokenize

from slicegate.config import Config
from slicegate.guards._common import Finding, expect, fixture, iter_files, read
from slicegate.messages import t

NAME = "naming_scope"
PACK = None
FAST = True
DEFECT = {"vi": "một khái niệm mang 2 tên ở 2 thứ tiếng ⇒ tìm kiếm/refactor sót chỗ, import nhầm",
          "en": "one concept with names in two languages ⇒ searches/refactors miss places, wrong imports"}

_C_COMMENT = re.compile(r"//[^\n]*|/\*.*?\*/", re.S)
_C_STRING = re.compile(r"`(?:\\.|[^`\\])*`|\"(?:\\.|[^\"\\\n])*\"|'(?:\\.|[^'\\\n])*'")
_IDENT = re.compile(r"[^\W\d]\w*", re.U)


def _non_ascii(name: str) -> bool:
    return any(ord(c) > 127 for c in name)


def names_in(rel: str, text: str) -> list[tuple[str, int]]:
    out: list[tuple[str, int]] = []
    if rel.endswith(".py"):
        try:
            for tok in tokenize.generate_tokens(io.StringIO(text).readline):
                if tok.type == tokenize.NAME and _non_ascii(tok.string):
                    out.append((tok.string, tok.start[0]))
        except (tokenize.TokenError, IndentationError, SyntaxError):
            pass
        return out
    blank = lambda m: re.sub(r"[^\n]", " ", m.group(0))  # giữ số dòng
    code = _C_STRING.sub(blank, _C_COMMENT.sub(blank, text))
    for i, line in enumerate(code.splitlines(), 1):
        for m in _IDENT.finditer(line):
            if _non_ascii(m.group(0)):
                out.append((m.group(0), i))
    return out


def _baseline(cfg: Config) -> set[str]:
    p = cfg.root / cfg["naming"]["baseline"]
    if not p.exists():
        return set()
    return {ln.strip() for ln in p.read_text(encoding="utf-8").splitlines() if ln.strip() and not ln.startswith("#")}


def check(cfg: Config) -> list[Finding]:
    base = _baseline(cfg)
    seen: set[str] = set()
    found: list[Finding] = []
    exts = tuple(cfg["paths"]["code_ext"])
    for rel in iter_files(cfg, exts=exts):
        if _non_ascii(rel.rsplit("/", 1)[-1]):
            found.append(Finding(NAME, rel, 0, t("naming.file_ascii")))
        for name, line in names_in(rel, read(cfg, rel)):
            key = f"{rel}:{name}"
            seen.add(key)
            if key not in base:
                found.append(Finding(NAME, rel, line, t("naming.ident", name=name)))
    for key in sorted(base - seen):
        found.append(Finding(NAME, cfg["naming"]["baseline"], 0, t("naming.baseline_stale", key=key)))
    return found


def selftest() -> list[str]:
    errs: list[str] = []
    with fixture({"src/a.py": "def tinh_tong(x):\n    # chú thích tiếng Việt được\n    return 'chuỗi có dấu'\n"}) as cfg:
        expect(errs, "py ASCII + chú thích Việt", check(cfg), red=False)
    with fixture({"src/a.py": "def tính_tổng(x):\n    return x\n"}) as cfg:
        expect(errs, "py tên có dấu", check(cfg), red=True)
    with fixture({"src/a.ts": "const giá = 1; // giá tiền\n"}) as cfg:
        expect(errs, "ts tên có dấu", check(cfg), red=True)
    with fixture({"src/a.ts": "const price = 'giá'; /* giá */\n"}) as cfg:
        expect(errs, "ts chuỗi + chú thích Việt", check(cfg), red=False)
    with fixture({"src/a.py": "giá = 1\n", ".slicegate/naming_baseline.txt": "src/a.py:giá\n"}) as cfg:
        expect(errs, "baseline miễn", check(cfg), red=False)
    with fixture({"src/a.py": "price = 1\n", ".slicegate/naming_baseline.txt": "src/a.py:giá\n"}) as cfg:
        expect(errs, "baseline cũ phải co", check(cfg), red=True)
    return errs
