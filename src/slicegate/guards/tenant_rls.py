"""Guard `tenant_rls` (gói saas_multitenant, bật bằng `packs.saas_multitenant.require_rls = true`) — lớp chặn thứ hai
ở Postgres: mỗi BẢNG TENANT phải `ENABLE ROW LEVEL SECURITY` và có ít nhất một `CREATE POLICY … ON <bảng>` trong migration.

Vì sao: truy vấn qua ORM, qua công cụ BI, qua tay quản trị — guard tĩnh `tenant_scope` không thấy hết. RLS bắt ở chính DB:
quên `WHERE tenant_id` thì vẫn chỉ thấy dữ liệu của tenant trong phiên.
"""
from __future__ import annotations

import re

from slicegate.config import Config
from slicegate.guards._common import Finding, expect, fixture, iter_files, read
from slicegate.guards.tenant_scope import _norm, tenant_tables
from slicegate.messages import t

NAME = "tenant_rls"
PACK = "saas_multitenant"
FAST = True
DEFECT = {"vi": "bảng của khách thuê không có RLS ⇒ một truy vấn qua ORM/BI/tay quên lọc là lộ dữ liệu mọi tenant",
          "en": "a tenant table without RLS ⇒ one ORM/BI/manual query missing the filter exposes every tenant's data"}

_ENABLE = re.compile(r"alter\s+table\s+(?:only\s+)?(?P<name>[\w.\"]+)\s+enable\s+row\s+level\s+security", re.I)
_POLICY = re.compile(r"create\s+policy\s+[\w\"]+\s+on\s+(?P<name>[\w.\"]+)", re.I)


def check(cfg: Config) -> list[Finding]:
    spec = cfg.pack("saas_multitenant")
    if not spec.get("require_rls"):
        return []
    tables, _ = tenant_tables(cfg)
    enabled: set[str] = set()
    policies: set[str] = set()
    first: dict[str, str] = {}
    for rel in iter_files(cfg, exts=(".sql",)):
        text = read(cfg, rel)
        enabled |= {_norm(m.group("name")) for m in _ENABLE.finditer(text)}
        policies |= {_norm(m.group("name")) for m in _POLICY.finditer(text)}
        for tb in tables:
            if tb not in first and re.search(rf"create\s+table\s+(?:if\s+not\s+exists\s+)?[\w.\"]*\b{re.escape(tb)}\b", text, re.I):
                first[tb] = rel
    found = []
    for tb in sorted(tables):
        if tb not in enabled:
            found.append(Finding(NAME, first.get(tb, ""), 0, t("rls.not_enabled", table=tb)))
        if tb not in policies:
            found.append(Finding(NAME, first.get(tb, ""), 0, t("rls.no_policy", table=tb)))
    return found


def selftest() -> list[str]:
    errs: list[str] = []
    on = {"project": {"packs": ["saas_multitenant"]}, "packs": {"saas_multitenant": {"require_rls": True}}}
    ddl = "CREATE TABLE invoices (\n  tenant_id uuid NOT NULL,\n  id bigint\n);\n"
    rls = ("ALTER TABLE invoices ENABLE ROW LEVEL SECURITY;\n"
           "CREATE POLICY tenant_isolation ON invoices USING (tenant_id = current_setting('app.tenant_id')::uuid);\n")
    with fixture({"db/0001.sql": ddl + rls}, on) as cfg:
        expect(errs, "bật RLS + policy", check(cfg), red=False)
    with fixture({"db/0001.sql": ddl}, on) as cfg:
        expect(errs, "thiếu RLS", check(cfg), red=True)
    with fixture({"db/0001.sql": ddl + "ALTER TABLE invoices ENABLE ROW LEVEL SECURITY;\n"}, on) as cfg:
        expect(errs, "bật RLS nhưng không policy", check(cfg), red=True)
    with fixture({"db/0001.sql": ddl}, {"project": {"packs": ["saas_multitenant"]}}) as cfg:
        expect(errs, "require_rls tắt", check(cfg), red=False)
    return errs
