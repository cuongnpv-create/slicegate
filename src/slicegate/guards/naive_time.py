"""Guard `naive_time` (gói logistics) — mốc thời gian luôn mang múi giờ.

Một chuyến hàng đi qua nhiều múi giờ: giờ cắt nhận hàng của kho, hạn giao (SLA), ETA, giờ hẹn lấy hàng. Mốc thời gian
"ngây thơ" (không múi giờ) được hiểu theo giờ của MÁY đang chạy ⇒ máy chủ ở UTC, kho ở GMT+7: đơn đặt 23:30 bị tính
sang ngày khác, SLA trễ 7 giờ mà không ai báo, phí phạt tính sai. Lưu UTC có múi giờ, đổi sang giờ địa phương khi hiển thị.

ĐỎ khi:
  · Python: `datetime.utcnow()` · `datetime.utcfromtimestamp(…)` (trả mốc ngây thơ) · `datetime.now()` / `.today()` /
    `.fromtimestamp(x)` không truyền múi giờ · `datetime(năm, tháng, ngày, …)` thiếu `tzinfo=`;
  · SQL: cột kiểu `timestamp` / `timestamp without time zone` (Postgres: dùng `timestamptz`) · `datetime` (MySQL);
  · JS/TS: `new Date("2026-10-26 08:00")` — chuỗi có giờ mà không có `Z` / `+07:00` ⇒ trình duyệt hiểu theo giờ máy.
Miễn từng chỗ: `naive-time: ignore <lý do>` trên cùng dòng hoặc dòng ngay trên.
"""
from __future__ import annotations

import ast
import re

from slicegate.config import Config
from slicegate.guards._common import Finding, expect, fixture, iter_files, read
from slicegate.messages import t

NAME = "naive_time"
PACK = "logistics"
FAST = True
DEFECT = {"vi": "mốc thời gian không múi giờ ⇒ giờ cắt, SLA, ETA lệch theo múi giờ của máy chủ",
          "en": "timestamps without a time zone ⇒ cut-offs, SLAs and ETAs shift by the server's time zone"}

_IGNORE = re.compile(r"naive-time:\s*ignore\s+\S", re.I)
_SQL_NAIVE = re.compile(r"^\s*\"?[A-Za-z_]\w*\"?\s+(?P<type>timestamp(?:\s*\(\d\))?(?!\s*(?:\(\d\)\s*)?with\s+time\s+zone)(?:\s+without\s+time\s+zone)?|datetime)\b",
                        re.I)
_JS_DATE = re.compile(r"new\s+Date\(\s*([\"'`])\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?\1")
_ALWAYS = {"utcnow", "utcfromtimestamp"}
_NEED_TZ = {"now": 0, "today": None, "fromtimestamp": 1}   # vị trí đối số tz (None = không nhận tz)


def _on_datetime(f: ast.AST) -> bool:
    """`datetime.x` hoặc `datetime.datetime.x` (⛔ `date.today()` — ngày không có giờ)."""
    if not isinstance(f, ast.Attribute):
        return False
    v = f.value
    return (isinstance(v, ast.Name) and v.id == "datetime") or (isinstance(v, ast.Attribute) and v.attr == "datetime")


def _is_ctor(f: ast.AST) -> bool:
    return (isinstance(f, ast.Name) and f.id == "datetime") or (isinstance(f, ast.Attribute) and f.attr == "datetime"
                                                                 and isinstance(f.value, ast.Name) and f.value.id == "datetime")


def _py(tree: ast.AST) -> list[tuple[int, str]]:
    out: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        f, kws = node.func, {k.arg for k in node.keywords}
        if _on_datetime(f) and f.attr in _ALWAYS:
            out.append((node.lineno, f"datetime.{f.attr}()"))
        elif _on_datetime(f) and f.attr in _NEED_TZ:
            pos = _NEED_TZ[f.attr]
            if "tz" not in kws and (pos is None or len(node.args) <= pos):
                out.append((node.lineno, f"datetime.{f.attr}()"))
        elif _is_ctor(f) and len(node.args) >= 3 and len(node.args) < 8 and "tzinfo" not in kws:
            out.append((node.lineno, "datetime(…)"))
    return out


def check(cfg: Config) -> list[Finding]:
    found: list[Finding] = []
    for rel in iter_files(cfg, exts=(".py", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".sql")):
        if not (cfg.is_prod(rel) or rel.endswith(".sql")):
            continue
        text = read(cfg, rel)
        lines = text.splitlines()
        if rel.endswith(".py"):
            try:
                hits = [(i, t("time.naive_py", call=c)) for i, c in _py(ast.parse(text))]
            except SyntaxError:
                continue
        elif rel.endswith(".sql"):
            hits = [(i, t("time.naive_sql", type=m.group("type").strip())) for i, line in enumerate(lines, 1)
                    if (m := _SQL_NAIVE.match(line.split("--", 1)[0]))]
        else:
            hits = [(i, t("time.naive_js")) for i, line in enumerate(lines, 1) if _JS_DATE.search(line)]
        for i, msg in hits:
            if not any(_IGNORE.search(x) for x in lines[max(i - 2, 0):i]):
                found.append(Finding(NAME, rel, i, msg))
    return found


def selftest() -> list[str]:
    errs: list[str] = []
    on = {"project": {"packs": ["logistics"]}}
    ok_py = ("from datetime import datetime, timezone\nimport datetime as dt\n"
             "def f(ts):\n    a = datetime.now(timezone.utc)\n    b = datetime.now(tz=timezone.utc)\n"
             "    c = datetime.fromtimestamp(ts, timezone.utc)\n    d = datetime(2026, 1, 1, tzinfo=timezone.utc)\n"
             "    e = dt.date.today()\n    return a, b, c, d, e\n")
    with fixture({"src/sla.py": ok_py}, on) as cfg:
        expect(errs, "mốc có múi giờ", check(cfg), red=False)
    with fixture({"src/sla.py": "from datetime import datetime\ndef f():\n    return datetime.utcnow()\n"}, on) as cfg:
        expect(errs, "utcnow trả mốc ngây thơ", check(cfg), red=True)
    with fixture({"src/sla.py": "import datetime\ndef f():\n    return datetime.datetime.now()\n"}, on) as cfg:
        expect(errs, "now() không múi giờ", check(cfg), red=True)
    with fixture({"src/sla.py": "from datetime import datetime\ndef f(ts):\n    return datetime.fromtimestamp(ts)\n"}, on) as cfg:
        expect(errs, "fromtimestamp không múi giờ", check(cfg), red=True)
    with fixture({"src/sla.py": "from datetime import datetime\nCUTOFF = datetime(2026, 10, 26, 17, 0)\n"}, on) as cfg:
        expect(errs, "datetime(...) thiếu tzinfo", check(cfg), red=True)
    with fixture({"src/sla.py": "from datetime import datetime\n# naive-time: ignore thư viện bên ngoài đòi mốc ngây thơ\nX = datetime.now()\n"}, on) as cfg:
        expect(errs, "miễn có lý do", check(cfg), red=False)
    with fixture({"db/1.sql": "CREATE TABLE shipments (\n  id uuid,\n  picked_at timestamptz,\n  due_at timestamp with time zone,\n  due_date date\n);\n"}, on) as cfg:
        expect(errs, "cột thời gian có múi giờ", check(cfg), red=False)
    with fixture({"db/1.sql": "CREATE TABLE shipments (\n  id uuid,\n  picked_at timestamp\n);\n"}, on) as cfg:
        expect(errs, "cột timestamp ngây thơ", check(cfg), red=True)
    with fixture({"db/1.sql": "CREATE TABLE shipments (\n  due_at timestamp(3) without time zone\n);\n"}, on) as cfg:
        expect(errs, "timestamp without time zone", check(cfg), red=True)
    with fixture({"frontend/src/eta.ts": "export const d = new Date('2026-10-26T08:00:00Z');\nexport const e = new Date(ms);\n"}, on) as cfg:
        expect(errs, "Date có Z", check(cfg), red=False)
    with fixture({"frontend/src/eta.ts": "export const d = new Date('2026-10-26 08:00');\n"}, on) as cfg:
        expect(errs, "Date chuỗi giờ không múi giờ", check(cfg), red=True)
    with fixture({"tests/test_sla.py": "from datetime import datetime\nX = datetime.now()\n"}, on) as cfg:
        expect(errs, "test không phải mã sản xuất", check(cfg), red=False)
    return errs
