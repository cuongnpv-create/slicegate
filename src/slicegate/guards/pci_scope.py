"""Guard `pci_scope` (gói ecommerce) — dữ liệu thẻ ⛔ được lưu trong hệ.

Lưu số thẻ đầy đủ / CVV / dải từ đưa cả hệ vào phạm vi PCI DSS; riêng CVV thì ⛔ bao giờ được lưu, kể cả mã hoá.
Cách đúng: cổng thanh toán giữ thẻ, hệ chỉ lưu token + 4 số cuối + hãng thẻ.

ĐỎ khi một cột SQL, trường ORM/dataclass/model, hoặc khoá JSON schema mang tên khớp `packs.ecommerce.card_names`
(mặc định: card_number · pan · cvv · cvc · cvv2 · card_cvc · track_data · magstripe). `last4`, `card_brand`,
`card_token`, `payment_method_id` ⛔ bị bắt.
"""
from __future__ import annotations

import ast
import re

from slicegate.config import Config
from slicegate.guards._common import Finding, expect, fixture, iter_files, read
from slicegate.messages import t

NAME = "pci_scope"
PACK = "ecommerce"
FAST = True
DEFECT = {"vi": "lưu số thẻ / CVV trong hệ ⇒ rò là lộ thẻ khách, cả hệ rơi vào phạm vi PCI DSS",
          "en": "card numbers / CVV stored in the system ⇒ a leak exposes customer cards and pulls the whole system into PCI DSS scope"}

_SQL_COL = re.compile(r"(?im)^\s*\"?(?P<col>[A-Za-z_]\w*)\"?\s+(?:text|varchar|char|character|bytea|blob|integer|bigint|numeric|string)\b")
_JSON_KEY = re.compile(r"\"(?P<key>[A-Za-z_]\w*)\"\s*:")


def check(cfg: Config) -> list[Finding]:
    rx = re.compile(cfg.pack("ecommerce")["card_names"])
    found: list[Finding] = []
    for rel in iter_files(cfg, exts=(".py", ".sql", ".json", ".prisma", ".ts")):
        if not (cfg.is_prod(rel) or rel.endswith((".sql", ".prisma"))):
            continue
        text = read(cfg, rel)
        if rel.endswith(".sql"):
            for m in _SQL_COL.finditer(text):
                if rx.fullmatch(m.group("col")):
                    found.append(Finding(NAME, rel, text.count("\n", 0, m.start()) + 1, t("pci.column", name=m.group("col"))))
        elif rel.endswith(".py"):
            try:
                tree = ast.parse(text)
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    for stmt in node.body:
                        target = stmt.target if isinstance(stmt, ast.AnnAssign) else (
                            stmt.targets[0] if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 else None)
                        if isinstance(target, ast.Name) and rx.fullmatch(target.id):
                            found.append(Finding(NAME, rel, stmt.lineno, t("pci.field", name=target.id, cls=node.name)))
        else:  # .json schema, .prisma, .ts kiểu/interface
            for i, line in enumerate(text.splitlines(), 1):
                keys = [m.group("key") for m in _JSON_KEY.finditer(line)] if rel.endswith(".json") else \
                    re.findall(r"^\s*([A-Za-z_]\w*)\??\s*[:\s]", line)
                for k in keys:
                    if rx.fullmatch(k):
                        found.append(Finding(NAME, rel, i, t("pci.field", name=k, cls=rel.rsplit("/", 1)[-1])))
    return found


def selftest() -> list[str]:
    errs: list[str] = []
    on = {"project": {"packs": ["ecommerce"]}}
    with fixture({"db/1.sql": "CREATE TABLE payment_methods (\n  card_token text,\n  last4 char(4),\n  card_brand text\n);\n"}, on) as cfg:
        expect(errs, "token + last4", check(cfg), red=False)
    with fixture({"db/1.sql": "CREATE TABLE payment_methods (\n  card_number varchar(19),\n  cvv char(4)\n);\n"}, on) as cfg:
        expect(errs, "card_number + cvv", check(cfg), red=True)
    with fixture({"src/models.py": "class Card(Model):\n    cvc: str\n    last4: str\n"}, on) as cfg:
        expect(errs, "trường cvc trong model", check(cfg), red=True)
    with fixture({"src/models.py": "class Card(Model):\n    last4 = CharField()\n    brand = CharField()\n"}, on) as cfg:
        expect(errs, "model không giữ thẻ", check(cfg), red=False)
    with fixture({"src/schema/payment.json": '{"properties": {"pan": {"type": "string"}}}'}, on) as cfg:
        expect(errs, "JSON schema có pan", check(cfg), red=True)
    with fixture({"src/types.ts": "interface Pay {\n  cardNumberMasked: string;\n  last4: string;\n}\n"}, on) as cfg:
        expect(errs, "TS chỉ có số che", check(cfg), red=False)
    with fixture({"src/types.ts": "interface Pay {\n  card_number: string;\n}\n"}, on) as cfg:
        expect(errs, "TS có card_number", check(cfg), red=True)
    return errs
