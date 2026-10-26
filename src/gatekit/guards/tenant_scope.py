"""Guard `tenant_scope` (gói saas_multitenant) — mọi dữ liệu của khách thuê mang tenant, mọi truy vấn lọc theo tenant.

Hai luật:
  1. DDL (tệp `.sql`): mỗi `CREATE TABLE` có cột `tenant_column`, ∨ chú thích `-- tenant: global <lý do>` (bảng dùng chung
     thật sự: gói cước, quốc gia…). Bảng có cột ấy là BẢNG TENANT.
  2. Truy vấn: mỗi câu SQL viết trong mã sản xuất (chuỗi Python / JS / TS / Go / Java…, và tệp `.sql` ngoài thư mục
     migration) mà chạm BẢNG TENANT (`FROM` · `JOIN` · `UPDATE` · `DELETE FROM` · `INSERT INTO`) phải nhắc tới
     `tenant_column` trong chính câu ấy. Miễn từng chỗ: chú thích `tenant-scope: ignore <lý do>` trên cùng dòng hoặc
     dòng ngay trên (job quản trị chạy xuyên tenant có chủ đích).
ORM (Django/SQLAlchemy/Prisma) không đọc được bằng tĩnh — dùng thêm RLS (`tenant_rls`) và test chéo tenant ở vùng K.
"""
from __future__ import annotations

import ast
import re

from gatekit.config import Config
from gatekit.guards._common import Finding, expect, fixture, iter_files, read
from gatekit.guards.partition_key_scope import _CREATE, _statement
from gatekit.messages import t

NAME = "tenant_scope"
PACK = "saas_multitenant"
FAST = True
DEFECT = {"vi": "truy vấn quên lọc tenant ⇒ khách thuê này đọc/sửa/xoá dữ liệu của khách thuê khác",
          "en": "a query forgets the tenant filter ⇒ one tenant reads/edits/deletes another tenant's data"}

_GLOBAL = re.compile(r"--\s*tenant:\s*global\s+\S", re.I)
_IGNORE = re.compile(r"tenant-scope:\s*ignore\s+\S", re.I)
_DML = re.compile(r"\b(select|update|delete|insert)\b", re.I)
_TABLE_REF = re.compile(r"\b(?:from|join|update|into)\s+(?P<name>[\w.\"`]+)", re.I)
_CODE_STR = re.compile(r"`(?:\\.|[^`\\])*`|\"(?:\\.|[^\"\\\n])*\"|'(?:\\.|[^'\\\n])*'")
_CODE_EXT = (".py", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".go", ".java", ".kt", ".rb", ".php", ".cs")


def _norm(name: str) -> str:
    return name.strip('"`').split(".")[-1].strip('"`').lower()


def tenant_tables(cfg: Config) -> tuple[set[str], list[Finding]]:
    spec = cfg.pack("saas_multitenant")
    col = re.compile(rf"(^|[\s(,]){re.escape(spec['tenant_column'])}\s+\w", re.I)
    tables: set[str] = set()
    found: list[Finding] = []
    for rel in iter_files(cfg, exts=(".sql",)):
        text = read(cfg, rel)
        for m in _CREATE.finditer(text):
            stmt = _statement(text, m.start())
            prev = text[:m.start()].rstrip().splitlines()[-1:] or [""]
            if col.search(stmt):
                tables.add(_norm(m.group("name")))
            elif not (_GLOBAL.search(stmt) or _GLOBAL.search(prev[0])):
                found.append(Finding(NAME, rel, text.count("\n", 0, m.start()) + 1,
                                     t("tenant.ddl", table=m.group("name"), column=spec["tenant_column"])))
    return tables, found


def _strings(rel: str, text: str) -> list[tuple[int, str]]:
    """(dòng, nội dung) của các chuỗi trong mã; Python đọc bằng AST (gồm f-string), ngôn ngữ khác bằng regex."""
    if rel.endswith(".py"):
        try:
            tree = ast.parse(text)
        except SyntaxError:
            return []
        out = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                out.append((node.lineno, node.value))
            elif isinstance(node, ast.JoinedStr):
                parts = [v.value for v in node.values if isinstance(v, ast.Constant) and isinstance(v.value, str)]
                out.append((node.lineno, " {} ".join(parts)))
        return out
    return [(text.count("\n", 0, m.start()) + 1, m.group(0)[1:-1]) for m in _CODE_STR.finditer(text)]


def check(cfg: Config) -> list[Finding]:
    spec = cfg.pack("saas_multitenant")
    tables, found = tenant_tables(cfg)
    if not tables:
        return found
    col = re.compile(rf"\b{re.escape(spec['tenant_column'])}\b", re.I)
    mig = re.compile(spec["migrations_regex"])
    for rel in iter_files(cfg, exts=_CODE_EXT + (".sql",)):
        if rel.endswith(".sql"):
            if mig.search(rel):
                continue
        elif not cfg.is_prod(rel):
            continue
        text = read(cfg, rel)
        lines = text.splitlines()
        if rel.endswith(".sql"):  # mỗi câu (tách bằng `;`) là một truy vấn
            items, start = [], 0
            for stmt in text.split(";"):
                items.append((text.count("\n", 0, start) + 1 + (len(stmt) - len(stmt.lstrip("\n"))), stmt))
                start += len(stmt) + 1
        else:
            items = _strings(rel, text)
        for line_no, sql in items:
            if not _DML.search(sql):
                continue
            hit = sorted({_norm(m.group("name")) for m in _TABLE_REF.finditer(sql)} & tables)
            if not hit or col.search(sql):
                continue
            near = " ".join(lines[max(0, line_no - 2):line_no])
            if _IGNORE.search(near):
                continue
            found.append(Finding(NAME, rel, line_no, t("tenant.query", tables=", ".join(hit), column=spec["tenant_column"])))
    return found


def selftest() -> list[str]:
    errs: list[str] = []
    on = {"project": {"packs": ["saas_multitenant"]}}
    ddl = ("CREATE TABLE invoices (\n  tenant_id uuid NOT NULL,\n  id bigint\n);\n"
           "-- tenant: global danh mục gói cước dùng chung\nCREATE TABLE plans (id int, name text);\n")
    with fixture({"db/migrations/0001.sql": ddl,
                  "src/repo.py": "def get(db, tid, i):\n    return db.q('SELECT * FROM invoices WHERE tenant_id = %s AND id = %s', tid, i)\n",
                  "src/plans.py": "def all(db):\n    return db.q('SELECT * FROM plans')\n"}, on) as cfg:
        expect(errs, "lọc tenant + bảng dùng chung", check(cfg), red=False)
    with fixture({"db/migrations/0001.sql": ddl,
                  "src/repo.py": "def get(db, i):\n    return db.q('SELECT * FROM invoices WHERE id = %s', i)\n"}, on) as cfg:
        expect(errs, "quên lọc tenant (py)", check(cfg), red=True)
    with fixture({"db/migrations/0001.sql": ddl,
                  "src/repo.ts": "export const del = (id) => db.query(`DELETE FROM invoices WHERE id = ${id}`);\n"}, on) as cfg:
        expect(errs, "quên lọc tenant (ts)", check(cfg), red=True)
    with fixture({"db/migrations/0001.sql": ddl,
                  "src/repo.py": "def f(db, t):\n    return db.q(f'UPDATE public.invoices SET paid = true WHERE tenant_id = {t}')\n"}, on) as cfg:
        expect(errs, "f-string có tenant_id + schema", check(cfg), red=False)
    with fixture({"db/migrations/0001.sql": ddl,
                  "src/jobs.py": "# tenant-scope: ignore job đối soát toàn hệ chạy bằng vai quản trị\nQ = 'SELECT count(*) FROM invoices'\n"}, on) as cfg:
        expect(errs, "miễn có lý do", check(cfg), red=False)
    with fixture({"db/migrations/0001.sql": ddl, "db/queries/report.sql": "SELECT sum(total) FROM invoices;\n"}, on) as cfg:
        expect(errs, "tệp .sql truy vấn quên tenant", check(cfg), red=True)
    with fixture({"db/migrations/0001.sql": "CREATE TABLE notes (id bigint, body text);\n"}, on) as cfg:
        expect(errs, "bảng thiếu cột tenant", check(cfg), red=True)
    with fixture({"db/migrations/0001.sql": ddl,
                  "tests/test_repo.py": "Q = 'SELECT * FROM invoices'\n"}, on) as cfg:
        expect(errs, "test không phải mã sản xuất", check(cfg), red=False)
    return errs
