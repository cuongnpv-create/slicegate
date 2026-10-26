"""Guard `unit_suffix` (gói logistics) — mỗi đại lượng vật lý mang ĐƠN VỊ trong tên.

`weight = 12` là 12 gì: kg hay lb? Một hãng vận chuyển nhận lb, kho ghi kg ⇒ cước lệch 2,2 lần, xe chở quá tải, hàng
lạnh hỏng vì °F đọc thành °C. Đơn vị nằm trong tên (`weight_kg`, `distanceKm`, `temp_c`) thì người đọc và người review
thấy ngay chỗ đổi đơn vị sai; chuyển đổi đi qua một module duy nhất.

ĐỎ khi một định danh là TÊN ĐẠI LƯỢNG — tách từ snake_case/camelCase, có từ trong `packs.logistics.quantity_words`
(weight, distance, length, volume, temperature…), ⛔ có từ trong `non_quantity_words` (unit, ratio, factor, type…) —
mà ⛔ có từ nào trong `unit_words` (kg, lb, km, mi, cbm, c, f…):
  · Python: tham số hàm, biến / thuộc tính được gán, trường có chú thích kiểu (`x = len(…)` không tính);
  · JS/TS: `const|let|var <tên> =`, trường `<tên>: number`;
  · SQL: cột trong `CREATE TABLE` / `ALTER TABLE … ADD COLUMN`.
Miễn từng chỗ: `units: ignore <lý do>` trên cùng dòng hoặc dòng ngay trên. Bỏ qua tệp khớp `unit_skip` (mặc định
`.tsx`/`.jsx`: `width`/`height` của thành phần giao diện là pixel bố cục, ⛔ kích thước hàng hoá).
"""
from __future__ import annotations

import ast
import re

from gatekit.config import Config
from gatekit.guards._common import Finding, expect, fixture, iter_files, read
from gatekit.guards.money_float import words
from gatekit.messages import t

NAME = "unit_suffix"
PACK = "logistics"
FAST = True
DEFECT = {"vi": "đại lượng không mang đơn vị ⇒ kg/lb, km/mi, °C/°F bị trộn: cước sai, xe quá tải, hàng lạnh hỏng",
          "en": "quantities without units ⇒ kg/lb, km/mi, °C/°F get mixed: wrong rates, overloaded vehicles, spoiled cold chain"}

_IGNORE = re.compile(r"units:\s*ignore\s+\S", re.I)
_JS_VAR = re.compile(r"\b(?:const|let|var)\s+(?P<name>[A-Za-z_$][\w$]*)\s*(?::[^=]+)?=")
_TS_FIELD = re.compile(r"^\s*(?:readonly\s+)?(?P<name>[A-Za-z_$][\w$]*)\??\s*:\s*number\b")
_SQL_COL = re.compile(r"^\s*(?:alter\s+table\s+[\w.\"]+\s+add\s+(?:column\s+)?(?:if\s+not\s+exists\s+)?)?\"?(?P<name>[A-Za-z_]\w*)\"?\s+"
                      r"[A-Za-z]\w*", re.I)
_SQL_KEYWORDS = {"create", "table", "primary", "constraint", "foreign", "unique", "check", "index", "alter", "insert",
                 "select", "update", "delete", "comment", "grant", "references", "on", "drop"}


def _spec(cfg: Config) -> tuple[set[str], set[str], set[str]]:
    pk = cfg.pack("logistics")
    return ({w.lower() for w in pk["quantity_words"]}, {w.lower() for w in pk["unit_words"]},
            {w.lower() for w in pk["non_quantity_words"]})


def lacks_unit(spec: tuple[set[str], set[str], set[str]], name: str) -> bool:
    ws = words(name)
    quantity, units, not_quantity = spec
    return bool(ws & quantity) and not (ws & not_quantity) and not (ws & units)


def _is_len(value: ast.AST | None) -> bool:
    return isinstance(value, ast.Call) and isinstance(value.func, ast.Name) and value.func.id == "len"


def _py_names(tree: ast.AST) -> list[tuple[int, str]]:
    out: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            a = node.args
            out += [(x.lineno, x.arg) for x in a.posonlyargs + a.args + a.kwonlyargs]
        elif isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)) and not _is_len(node.value):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for tg in targets:
                for x in ast.walk(tg):
                    if isinstance(x, ast.Name) and isinstance(x.ctx, ast.Store):
                        out.append((x.lineno, x.id))
                    elif isinstance(x, ast.Attribute) and isinstance(x.ctx, ast.Store):
                        out.append((x.lineno, x.attr))
    return out


def check(cfg: Config) -> list[Finding]:
    spec = _spec(cfg)
    skip = [re.compile(p) for p in cfg.pack("logistics")["unit_skip"]]
    found: list[Finding] = []
    for rel in iter_files(cfg, exts=(".py", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".sql")):
        if not (cfg.is_prod(rel) or rel.endswith(".sql")) or any(p.search(rel) for p in skip):
            continue
        text = read(cfg, rel)
        lines = text.splitlines()
        if rel.endswith(".py"):
            try:
                names = _py_names(ast.parse(text))
            except SyntaxError:
                continue
        elif rel.endswith(".sql"):
            names = [(i, m.group("name")) for i, line in enumerate(lines, 1)
                     if (m := _SQL_COL.match(line.split("--", 1)[0])) and m.group("name").lower() not in _SQL_KEYWORDS]
        else:
            names = [(i, m.group("name")) for i, line in enumerate(lines, 1)
                     for rx in (_JS_VAR, _TS_FIELD) for m in rx.finditer(line)]
        seen: set[tuple[int, str]] = set()
        for i, name in sorted(names):
            if (i, name) in seen or not lacks_unit(spec, name):
                continue
            seen.add((i, name))
            near = lines[max(i - 2, 0):i]
            if any(_IGNORE.search(x) for x in near):
                continue
            found.append(Finding(NAME, rel, i, t("unit.missing", name=name)))
    return found


def selftest() -> list[str]:
    errs: list[str] = []
    on = {"project": {"packs": ["logistics"]}}
    with fixture({"src/rate.py": "def quote(weight_kg, distance_km, dim_divisor, weight_unit):\n    n = len(items)\n    return weight_kg\n"}, on) as cfg:
        expect(errs, "tên có đơn vị + từ loại trừ", check(cfg), red=False)
    with fixture({"src/rate.py": "def quote(weight, distance_km):\n    return weight\n"}, on) as cfg:
        expect(errs, "tham số weight không đơn vị", check(cfg), red=True)
    with fixture({"src/parcel.py": "class Parcel:\n    def __init__(self, w):\n        self.gross_weight = w\n"}, on) as cfg:
        expect(errs, "thuộc tính gán không đơn vị", check(cfg), red=True)
    with fixture({"src/parcel.py": "from dataclasses import dataclass\n@dataclass\nclass Parcel:\n    lengthCm: int\n    widthCm: int\n    volume: float\n"}, on) as cfg:
        expect(errs, "trường dataclass volume không đơn vị", check(cfg), red=True)
    with fixture({"src/util.py": "def pad(xs):\n    length = len(xs)\n    return length\n"}, on) as cfg:
        expect(errs, "length = len(...) là số phần tử", check(cfg), red=False)
    with fixture({"src/util.py": "def pad(xs, length):  # units: ignore độ dài chuỗi, không phải kích thước\n    return xs\n"}, on) as cfg:
        expect(errs, "miễn có lý do", check(cfg), red=False)
    with fixture({"frontend/src/eta.ts": "export const distance = route.total;\n"}, on) as cfg:
        expect(errs, "const distance không đơn vị", check(cfg), red=True)
    with fixture({"frontend/src/eta.ts": "interface Leg {\n  distanceKm: number;\n  temperature?: number;\n}\n"}, on) as cfg:
        expect(errs, "trường TS temperature: number", check(cfg), red=True)
    with fixture({"frontend/src/eta.ts": "interface Leg {\n  distanceKm: number;\n  tempC?: number;\n  heightPx: number;\n}\n"}, on) as cfg:
        expect(errs, "trường TS có đơn vị", check(cfg), red=False)
    with fixture({"frontend/src/Map.tsx": "interface P {\n  width: number;\n  height: number;\n}\n"}, on) as cfg:
        expect(errs, "thành phần giao diện .tsx bỏ qua", check(cfg), red=False)
    with fixture({"frontend/src/Map.tsx": "interface P {\n  width: number;\n}\n"},
                 {"project": {"packs": ["logistics"]}, "packs": {"logistics": {"unit_skip": []}}}) as cfg:
        expect(errs, "unit_skip rỗng thì .tsx bị xét", check(cfg), red=True)
    with fixture({"db/1.sql": "CREATE TABLE parcels (\n  id uuid,\n  weight numeric(10,3)\n);\n"}, on) as cfg:
        expect(errs, "cột SQL weight không đơn vị", check(cfg), red=True)
    with fixture({"db/1.sql": "CREATE TABLE parcels (\n  id uuid,\n  weight_g integer,\n  volume_cbm numeric\n);\n"}, on) as cfg:
        expect(errs, "cột SQL có đơn vị", check(cfg), red=False)
    with fixture({"tests/test_rate.py": "weight = 3\n"}, on) as cfg:
        expect(errs, "test không phải mã sản xuất", check(cfg), red=False)
    return errs
