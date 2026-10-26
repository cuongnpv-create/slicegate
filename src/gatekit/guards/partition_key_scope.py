"""Guard `partition_key_scope` (gói multi_provider) — mọi bảng mang cột phân vùng (`provider` / `tenant_id`…).

Mỗi `CREATE TABLE` trong tệp SQL phải: có cột `partition_column`, ∨ mang chú thích miễn `-- partition: global <lý do>`
ngay trên hoặc trong câu lệnh (bảng tra cứu dùng chung thật sự). Thiếu ⇒ ĐỎ.
"""
from __future__ import annotations

import re

from gatekit.config import Config
from gatekit.guards._common import Finding, expect, fixture, iter_files, read

NAME = "partition_key_scope"
PACK = "multi_provider"
FAST = True
DEFECT = "dữ liệu của hai nhà cung cấp/khách hàng trộn chung một khoá ⇒ ghi đè, đọc nhầm, rò dữ liệu chéo"

_CREATE = re.compile(r"create\s+(?:unlogged\s+|temp(?:orary)?\s+)?table\s+(?:if\s+not\s+exists\s+)?(?P<name>[\w.\"]+)\s*\(",
                     re.I)
_EXEMPT = re.compile(r"--\s*partition:\s*global\s+\S", re.I)


def _statement(text: str, start: int) -> str:
    depth, i = 0, text.index("(", start)
    for j in range(i, len(text)):
        if text[j] == "(":
            depth += 1
        elif text[j] == ")":
            depth -= 1
            if depth == 0:
                return text[start:j + 1]
    return text[start:]


def check(cfg: Config) -> list[Finding]:
    spec = cfg.pack("multi_provider")
    col = re.compile(rf"(^|[\s(,]){re.escape(spec['partition_column'])}\s+\w", re.I)
    found: list[Finding] = []
    for rel in iter_files(cfg):
        if not any(re.search(g, rel) for g in spec["sql_globs"]):
            continue
        text = read(cfg, rel)
        for m in _CREATE.finditer(text):
            stmt = _statement(text, m.start())
            prev = text[:m.start()].rstrip().splitlines()[-1:] or [""]
            if col.search(stmt) or _EXEMPT.search(stmt) or _EXEMPT.search(prev[0]):
                continue
            line = text.count("\n", 0, m.start()) + 1
            found.append(Finding(NAME, rel, line,
                                 f"bảng `{m.group('name')}` thiếu cột `{spec['partition_column']}` (∨ chú thích `-- partition: global <lý do>`)"))
    return found


def selftest() -> list[str]:
    errs: list[str] = []
    on = {"project": {"packs": ["multi_provider"]}}
    with fixture({"db/1.sql": "CREATE TABLE orders (\n  provider text NOT NULL,\n  id bigint\n);\n"}, on) as cfg:
        expect(errs, "có cột", check(cfg), red=False)
    with fixture({"db/1.sql": "CREATE TABLE orders (id bigint, amount numeric);\n"}, on) as cfg:
        expect(errs, "thiếu cột", check(cfg), red=True)
    with fixture({"db/1.sql": "-- partition: global bảng tiền tệ ISO dùng chung\nCREATE TABLE currencies (code text);\n"}, on) as cfg:
        expect(errs, "miễn có lý do", check(cfg), red=False)
    with fixture({"db/1.sql": "-- partition: global\nCREATE TABLE currencies (code text);\n"}, on) as cfg:
        expect(errs, "miễn thiếu lý do", check(cfg), red=True)
    return errs
