"""Guard `money_float` (gói ecommerce) — tiền ⛔ là số thực dấu phẩy động.

`0.1 + 0.2 != 0.3`: cộng dồn giá, chia phần giảm giá, làm tròn thuế bằng float lệch vài xu ⇒ tổng đơn ≠ tổng thanh toán,
đối soát lệch, hoàn tiền sai. Tiền là số nguyên đơn vị nhỏ nhất (xu/đồng) hoặc thập phân chính xác (`Decimal`, `NUMERIC`).

ĐỎ khi một định danh là TÊN TIỀN — tách từ theo snake_case/camelCase, có từ trong `packs.ecommerce.money_words`
(price, amount, total, tax, fee, discount…) và ⛔ có từ trong `non_money_words` (weight, qty, rate, percent… —
`total_weight`, `tax_rate`, `discountPercent` là số thực hợp lệ):
  · Python: chú thích kiểu `float` (`price: float`, `-> float` của hàm tên tiền), hoặc `float(<tên tiền>)`;
  · JS/TS: `parseFloat(<tên tiền>)`, `<tên tiền>: number` không bị ĐỎ (TS không có kiểu thập phân) — chỉ bắt parseFloat;
  · SQL: cột tên tiền kiểu `FLOAT` · `REAL` · `DOUBLE PRECISION` · `DOUBLE`.
"""
from __future__ import annotations

import ast
import re

from slicegate.config import Config
from slicegate.guards._common import Finding, expect, fixture, iter_files, read
from slicegate.messages import t

NAME = "money_float"
PACK = "ecommerce"
FAST = True
DEFECT = {"vi": "tiền tính bằng số thực ⇒ tổng đơn lệch tổng thanh toán vài xu, đối soát và hoàn tiền sai",
          "en": "money computed in floating point ⇒ order total and charged amount drift by cents, reconciliation and refunds go wrong"}

_SQL_COL = re.compile(r"(?im)^\s*\"?(?P<col>[A-Za-z_]\w*)\"?\s+(?P<type>float\d*|real|double(?:\s+precision)?)\b")
_JS_PARSE = re.compile(r"parseFloat\(\s*(?:[\w.]*\.)?(?P<name>[A-Za-z_]\w*)")


def words(name: str) -> set[str]:
    return {w.lower() for w in re.findall(r"[A-Z]?[a-z]+|[A-Z]+(?![a-z])|\d+", name)}


def _is_money(spec: tuple[set[str], set[str]], name: str) -> bool:
    ws = words(name)
    money, not_money = spec
    return bool(ws & money) and not (ws & not_money)


def _ann_is_float(node: ast.AST | None) -> bool:
    if node is None:
        return False
    if isinstance(node, ast.Name):
        return node.id == "float"
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value == "float"
    if isinstance(node, ast.BinOp):  # float | None
        return _ann_is_float(node.left) or _ann_is_float(node.right)
    if isinstance(node, ast.Subscript):  # Optional[float]
        return _ann_is_float(node.slice)
    return False


def _name_of(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return ""


def check(cfg: Config) -> list[Finding]:
    pk = cfg.pack("ecommerce")
    rx = ({w.lower() for w in pk["money_words"]}, {w.lower() for w in pk["non_money_words"]})
    found: list[Finding] = []
    for rel in iter_files(cfg, exts=(".py", ".ts", ".tsx", ".js", ".jsx", ".sql")):
        if not (cfg.is_prod(rel) or rel.endswith(".sql")):
            continue
        text = read(cfg, rel)
        if rel.endswith(".py"):
            try:
                tree = ast.parse(text)
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.AnnAssign) and _ann_is_float(node.annotation):
                    name = _name_of(node.target)
                    if _is_money(rx, name):
                        found.append(Finding(NAME, rel, node.lineno, t("money.annotation", name=name)))
                elif isinstance(node, ast.arg) and _ann_is_float(node.annotation) and _is_money(rx, node.arg):
                    found.append(Finding(NAME, rel, node.lineno, t("money.annotation", name=node.arg)))
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and _ann_is_float(node.returns) \
                        and _is_money(rx, node.name):
                    found.append(Finding(NAME, rel, node.lineno, t("money.returns", name=node.name)))
                elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "float" \
                        and node.args and _is_money(rx, _name_of(node.args[0])):
                    found.append(Finding(NAME, rel, node.lineno, t("money.cast", name=_name_of(node.args[0]))))
        elif rel.endswith(".sql"):
            for m in _SQL_COL.finditer(text):
                if _is_money(rx, m.group("col")):
                    line = text.count("\n", 0, m.start()) + 1
                    found.append(Finding(NAME, rel, line, t("money.sql", name=m.group("col"), type=m.group("type").upper())))
        else:
            for i, line in enumerate(text.splitlines(), 1):
                for m in _JS_PARSE.finditer(line):
                    if _is_money(rx, m.group("name")):
                        found.append(Finding(NAME, rel, i, t("money.parse_float", name=m.group("name"))))
    return found


def selftest() -> list[str]:
    errs: list[str] = []
    on = {"project": {"packs": ["ecommerce"]}}
    with fixture({"src/cart.py": "from decimal import Decimal\ndef total(items) -> Decimal:\n    price: Decimal = Decimal('1.10')\n    weight: float = 2.5\n    return price\n"}, on) as cfg:
        expect(errs, "Decimal + float cho trọng lượng", check(cfg), red=False)
    with fixture({"src/cart.py": "price: float = 1.10\n"}, on) as cfg:
        expect(errs, "price: float", check(cfg), red=True)
    with fixture({"src/cart.py": "def apply(discount: float | None):\n    pass\n"}, on) as cfg:
        expect(errs, "tham số discount: float | None", check(cfg), red=True)
    with fixture({"src/cart.py": "def order_total(items) -> float:\n    return 0\n"}, on) as cfg:
        expect(errs, "hàm tiền trả float", check(cfg), red=True)
    with fixture({"src/cart.py": "x = float(item.unit_price)\n"}, on) as cfg:
        expect(errs, "float(unit_price)", check(cfg), red=True)
    with fixture({"src/cart.ts": "const t = parseFloat(form.amount);\n"}, on) as cfg:
        expect(errs, "parseFloat(amount)", check(cfg), red=True)
    with fixture({"db/1.sql": "CREATE TABLE orders (\n  id bigint,\n  total_amount DOUBLE PRECISION,\n  weight real\n);\n"}, on) as cfg:
        expect(errs, "cột tiền DOUBLE", check(cfg), red=True)
    with fixture({"db/1.sql": "CREATE TABLE orders (\n  total_amount NUMERIC(12,2),\n  weight real\n);\n"}, on) as cfg:
        expect(errs, "NUMERIC + real cho trọng lượng", check(cfg), red=False)
    with fixture({"src/ship.py": "total_weight: float = 1.0\ntax_rate: float = 0.1\ndef f(discountPercent: float): pass\n"}, on) as cfg:
        expect(errs, "trọng lượng / tỷ lệ / phần trăm", check(cfg), red=False)
    with fixture({"src/cart.py": "def f(unitPrice: float): pass\n"}, on) as cfg:
        expect(errs, "camelCase unitPrice", check(cfg), red=True)
    with fixture({"tests/test_cart.py": "price: float = 1.1\n"}, on) as cfg:
        expect(errs, "test không phải mã sản xuất", check(cfg), red=False)
    return errs
